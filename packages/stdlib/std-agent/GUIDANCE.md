# std-agent Module Guidance

## Purpose
The `packages/stdlib/std-agent/` module provides core agent primitives for Diamond—the foundational abstractions for building autonomous agents with structured decision-making, prompt management, and tool orchestration. This module is central to Diamond's identity as an agent-native language. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), capability discipline, and agentic philosophy.
- **`diamond2.md`** — Architectural feasibility, zero-trust execution, and LLM integration patterns.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, and module-level capability injection.

The `std-agent` module exemplifies Diamond's vision: making agent development safe, expressive, and semantically precise.

---

## Directory Contract

| Path | Purpose |
| --- | --- |
| `src/lib.dm` | Module root, public API exports. |
| `src/prompt.dm` | Prompt construction, templates, and validation. |
| `src/decision.dm` | Decision operator utilities, branch routing, semantic selection. |
| `src/tool.dm` | Tool declaration, invocation, and result handling. |
| `src/context.dm` | Agent context management, conversation state, memory. |
| `src/lifecycle.dm` | Agent lifecycle hooks, initialization, cleanup. |
| `src/types.dm` | Core agent type definitions and semantic types. |
| `src/effects.dm` | Agent-specific effect declarations (LLM, Tool). |
| `capabilities.toml` | Required capability declarations. |
| `tests/` | Comprehensive test suites. |
| `examples/` | Usage examples for each major feature. |
| `README.md` | Module documentation and API reference. |
| `GUIDANCE.md` | This file—contribution and quality standards. |

---

## Core Abstractions

### Prompt Types

```diamond
/// A structured prompt with typed placeholders.
type Prompt = {
    template: String,
    variables: Map[String, PromptValue],
    constraints: List[OutputConstraint],
}

/// Values that can be interpolated into prompts.
enum PromptValue {
    Text(String),
    Number(Float),
    Boolean(Bool),
    List(List[PromptValue]),
    Structured(Map[String, PromptValue]),
}

/// Constraints on LLM output for structured generation.
enum OutputConstraint {
    JsonSchema(Schema),
    Regex(Pattern),
    Enum(List[String]),
    SemanticType(TypeId),
}
```

### Decision Utilities

```diamond
/// Metadata for decision operator branches.
type BranchMetadata = {
    label: String,
    confidence_threshold: Option[Float],
    semantic_description: String,
    fallback: Bool,
}

/// Result of a decision operation.
type DecisionResult[T] = {
    selected_branch: String,
    value: T,
    confidence: Float,
    reasoning: Option[String],
}

/// Helper for constructing decision blocks with metadata.
fn decision_with_metadata[T](
    branches: List[(BranchMetadata, () -> T)]
) -> T performs LLM { ... }
```

### Tool Abstractions

```diamond
/// Declaration of a tool available to the agent.
type Tool = {
    name: String,
    description: String,
    parameters: Schema,
    returns: Schema,
    capability: Option[CapabilityId],
}

/// Result of a tool invocation.
type ToolResult[T] = Result[T, ToolError]

/// Errors that can occur during tool invocation.
enum ToolError {
    NotFound(String),
    InvalidArguments(String),
    CapabilityDenied(CapabilityId),
    ExecutionFailed(String),
    Timeout,
}
```

### Agent Context

```diamond
/// Conversation context for multi-turn agents.
type ConversationContext = {
    messages: List[Message],
    metadata: Map[String, Value],
    token_count: Int,
    max_tokens: Int,
}

/// A message in a conversation.
type Message = {
    role: Role,
    content: String,
    timestamp: Timestamp,
    metadata: Map[String, Value],
}

/// Message roles in a conversation.
enum Role {
    System,
    User,
    Assistant,
    Tool(String),
}
```

---

## Effect Declarations

The `std-agent` module declares agent-specific effects:

```diamond
/// Effect for LLM operations.
effect LLM {
    /// Complete a prompt with the configured model.
    fn complete(prompt: Prompt) -> String
    
    /// Complete with structured output.
    fn complete_structured[T](prompt: Prompt, schema: Schema) -> T
    
    /// Generate embeddings for text.
    fn embed(text: String) -> List[Float]
    
    /// Classify text into categories.
    fn classify(text: String, categories: List[String]) -> String
    
    /// Estimate token count for text.
    fn count_tokens(text: String) -> Int
}

/// Effect for tool invocation.
effect Tool {
    /// Invoke a registered tool.
    fn invoke[T](tool: String, args: Map[String, Value]) -> ToolResult[T]
    
    /// List available tools.
    fn list_tools() -> List[Tool]
    
    /// Check if a tool is available.
    fn has_tool(name: String) -> Bool
}

/// Effect for agent memory operations.
effect Memory {
    /// Store a value in agent memory.
    fn store(key: String, value: Value) -> ()
    
    /// Retrieve a value from memory.
    fn retrieve(key: String) -> Option[Value]
    
    /// Search memory by semantic similarity.
    fn search(query: String, limit: Int) -> List[(String, Value, Float)]
}
```

---

## Capability Requirements

The module requires these capabilities:

```toml
# capabilities.toml
[module]
name = "std-agent"
version = "0.1.0"
stability = "experimental"

[[required_capabilities]]
capability = "LLM"
permissions = ["complete", "embed", "classify"]
justification = "Core agent functionality requires LLM access"

[[optional_capabilities]]
capability = "Tool"
permissions = ["invoke"]
justification = "Tool orchestration requires tool invocation capability"

[[optional_capabilities]]
capability = "Memory"
permissions = ["read", "write"]
justification = "Persistent agent memory requires memory capability"
```

---

## API Design Principles

### 1. Composable Primitives
Provide small, focused functions that compose well:

```diamond
// Compose prompt building
let prompt = prompt_builder()
    .system("You are a helpful assistant.")
    .user(user_input)
    .with_constraint(JsonSchema(response_schema))
    .build()

// Compose tool pipelines
let result = tool_pipeline()
    .call("search", { query: question })
    .then("summarize", |results| { text: results })
    .execute()
```

### 2. Type-Safe LLM Interaction
Leverage semantic types for structured generation:

```diamond
/// Parse LLM output as a validated email.
fn extract_email(text: String) -> Email performs LLM {
    perform LLM.complete_structured[Email](
        prompt("Extract the email address from: {text}")
            .with_constraint(SemanticType(Email)),
        email_schema()
    )
}
```

### 3. Decision Operator Support
Provide utilities that enhance the `<>` operator:

```diamond
/// Execute a decision with logging and fallback.
fn decide_with_fallback[T](
    decision: () -> T performs LLM,
    fallback: () -> T,
    logger: Option[Logger],
) -> T performs LLM {
    try {
        let result = decision()
        logger.map(|l| l.info("Decision succeeded"))
        result
    } catch {
        logger.map(|l| l.warn("Decision failed, using fallback"))
        fallback()
    }
}
```

### 4. Resumable Agent Workflows
Design for continuation across LLM calls:

```diamond
/// Agent that can be suspended and resumed.
fn resumable_agent(
    initial_context: ConversationContext,
) -> AgentResult performs LLM, Tool, Memory {
    let context = initial_context
    
    loop {
        // This perform may suspend the agent
        let response = perform LLM.complete(
            context.to_prompt()
        )
        
        // Check for tool calls
        match parse_tool_call(response) {
            Some(tool_call) => {
                let result = perform Tool.invoke(
                    tool_call.name,
                    tool_call.args
                )
                context.add_tool_result(tool_call.name, result)
            }
            None => {
                // Final response
                return AgentResult.complete(response)
            }
        }
    }
}
```

---

## Testing Requirements

### Unit Tests
- Test prompt construction and validation.
- Test tool result parsing.
- Test context management logic.
- Test semantic type constraints.

### Effect Mocking
Provide mock handlers for testing:

```diamond
/// Mock LLM handler for testing.
handler MockLLMHandler for LLM {
    responses: List[String],
    index: Int,
    
    fn complete(prompt, resume) {
        let response = self.responses[self.index % self.responses.len()]
        self.index += 1
        resume(response)
    }
    
    fn complete_structured[T](prompt, schema, resume) {
        // Return typed mock response
        resume(self.mock_structured[T]())
    }
}

// Usage in tests
test "agent handles tool calls" {
    with MockLLMHandler(responses: ["[tool:search] query"]) {
        with MockToolHandler(tools: mock_tools()) {
            let result = resumable_agent(initial_context())
            assert(result.tool_calls.len() == 1)
        }
    }
}
```

### Integration Tests
- Test full agent workflows with mock LLM.
- Test tool orchestration patterns.
- Test context persistence across suspensions.

### Property Tests
- Prompt templates produce valid prompts for all inputs.
- Tool results parse correctly for all valid schemas.
- Context token counting is accurate.

---

## Documentation Standards

Every public item must document:

1. **Purpose**: What the function/type does.
2. **Parameters**: Each parameter's type and meaning.
3. **Returns**: Return type and semantics.
4. **Effects**: Which effects are performed.
5. **Capabilities**: Which capabilities are required.
6. **Examples**: Runnable usage examples.
7. **Errors**: Possible error conditions.

### Example Documentation

```diamond
/// Build a prompt from a template with variable substitution.
///
/// # Arguments
/// * `template` - The prompt template with {variable} placeholders.
/// * `variables` - Map of variable names to values.
///
/// # Returns
/// A validated Prompt ready for LLM completion.
///
/// # Errors
/// * `PromptError::MissingVariable` - Template references undefined variable.
/// * `PromptError::InvalidTemplate` - Template syntax is malformed.
///
/// # Example
/// ```diamond
/// let prompt = build_prompt(
///     "Hello, {name}! How can I help with {topic}?",
///     { "name": "Alice", "topic": "Diamond programming" }
/// )
/// ```
///
/// @stability stable
/// @since 0.1.0
fn build_prompt(
    template: String,
    variables: Map[String, PromptValue],
) -> Result[Prompt, PromptError] { ... }
```

---

## Security Considerations

### Prompt Injection Prevention
- Validate and sanitize user inputs in prompts.
- Provide escaping utilities for untrusted data.
- Document injection risks in prompt APIs.

### Capability Hygiene
- Never request more capabilities than needed.
- Document capability requirements for each function.
- Provide capability-minimal alternatives.

### Tool Invocation Safety
- Validate tool arguments against schemas.
- Enforce capability checks before tool execution.
- Log all tool invocations for audit.

---

## Quality Checklist (Pre-Merge)

- [ ] All public items have comprehensive documentation.
- [ ] Effects are declared and documented.
- [ ] Capabilities are declared in manifest.
- [ ] Unit tests cover all public functions.
- [ ] Mock handlers provided for testing.
- [ ] Examples demonstrate idiomatic usage.
- [ ] Security considerations addressed.
- [ ] Prompt injection risks documented.
- [ ] Error handling is comprehensive.
- [ ] Code follows Diamond conventions.
- [ ] README is complete and accurate.
- [ ] CHANGELOG updated for changes.

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the feature.
   - Discuss API design with Language WG.
   - Consider security implications.

2. **Implementation**
   - Follow the module structure.
   - Write tests alongside code.
   - Include examples for new features.
   - Document all public APIs.

3. **Review**
   - Request Language WG review.
   - Address feedback on API design.
   - Ensure effect and capability hygiene.
   - Verify security considerations.

4. **Publication**
   - Update README and CHANGELOG.
   - Add to stdlib index.
   - Announce in release notes.

---

## Future Enhancements

- ReAct loop primitives for reasoning+acting patterns.
- Multi-agent coordination utilities.
- Streaming response handling.
- Token budget management.
- Conversation summarization.
- Agent observability and debugging tools.
- Prompt versioning and A/B testing support.

---

The `std-agent` module is Diamond's flagship—demonstrating that agent development can be safe, typed, and elegant. Every abstraction should make agents easier to build correctly and harder to build insecurely.