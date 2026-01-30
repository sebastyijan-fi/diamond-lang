# Prompt Packs Guidance

## Purpose
The `packages/tooling/prompt-packs/` directory contains curated prompt templates for LLM-assisted Diamond development. These prompt packs enable consistent, high-quality AI interactions for code generation, review, debugging, and documentation tasks. All content must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Synthetic bootstrapping strategy, LLM integration patterns, and ML enablement pipelines.
- **`diamond3.md`** — Grammar specification, semantic typing, and module-level capability injection.

Prompt packs are the interface between Diamond's language design and LLM capabilities—ensuring AI assistance produces idiomatic, secure, capability-aware code.

---

## Directory Structure

```
prompt-packs/
├── README.md                    # Overview, usage guide, contribution instructions
├── GUIDANCE.md                  # This file
├── index.yaml                   # Registry of all available prompt packs
├── code-generation/             # Prompts for generating Diamond code
│   ├── metadata.yaml            # Pack metadata and configuration
│   ├── system.txt               # System prompt template
│   ├── user_template.txt        # User message template
│   ├── examples/                # Few-shot examples
│   └── tests/                   # Prompt validation tests
├── code-review/                 # Prompts for reviewing Diamond code
├── debugging/                   # Prompts for debugging assistance
├── documentation/               # Prompts for generating documentation
├── refactoring/                 # Prompts for code refactoring
├── explanation/                 # Prompts for explaining Diamond concepts
├── conversion/                  # Prompts for converting to/from Diamond
└── testing/                     # Prompts for generating tests
```

---

## Pack Categories

### Code Generation
Generate Diamond code from natural language descriptions.

**Use Cases:**
- Function implementation from signatures
- Agent workflow generation
- Effect handler creation
- Module scaffolding

### Code Review
Review Diamond code for correctness, security, and best practices.

**Use Cases:**
- Capability hygiene validation
- Effect handling review
- Security vulnerability detection
- Style and convention checks

### Debugging
Assist with debugging Diamond code issues.

**Use Cases:**
- Error message interpretation
- Root cause analysis
- Fix suggestions
- Runtime behavior explanation

### Documentation
Generate documentation for Diamond code.

**Use Cases:**
- Doc comment generation
- README creation
- API reference generation
- Example code generation

### Refactoring
Suggest and implement code refactoring.

**Use Cases:**
- Effect extraction
- Capability minimization
- Code deduplication
- Pattern application

### Explanation
Explain Diamond concepts and code.

**Use Cases:**
- Syntax explanation
- Effect system explanation
- Capability model explanation
- Code walkthrough

### Conversion
Convert code to or from Diamond.

**Use Cases:**
- Python to Diamond conversion
- TypeScript to Diamond conversion
- Diamond to pseudocode
- Legacy code modernization

### Testing
Generate tests for Diamond code.

**Use Cases:**
- Unit test generation
- Property test generation
- Effect mock generation
- Integration test scaffolding

---

## Pack Metadata Format

Every prompt pack includes a `metadata.yaml` file:

```yaml
name: "code-generation"
version: "1.0.0"
description: "Generate idiomatic Diamond code from natural language descriptions"
authors:
  - "Diamond Team <team@diamond-lang.org>"

# Target LLM models
models:
  primary:
    - "gpt-4"
    - "claude-3-opus"
    - "claude-3-sonnet"
  tested:
    - "gpt-4-turbo"
    - "claude-3-haiku"
  future:
    - "diamond-llama"  # Custom Diamond-trained model

# Capability requirements for generated code
code_capabilities:
  allowed:
    - "Console"
    - "FileSystem"
    - "Network"
    - "LLM"
    - "Time"
  restricted:
    - "Crypto"  # Requires explicit user confirmation
  forbidden:
    - "System"  # Never generate system access

# Safety constraints
safety:
  - "no_capability_escalation"
  - "no_ambient_authority"
  - "explicit_error_handling"
  - "no_secret_embedding"
  - "input_validation_required"

# Quality expectations
quality:
  include_doc_comments: true
  include_examples: true
  include_tests: false
  max_function_length: 50
  require_type_annotations: true

# Dependencies
requires_context:
  - "diamond_grammar"      # Grammar reference
  - "capability_model"     # Capability documentation
  - "effect_patterns"      # Common effect patterns

last_updated: "2025-01-15"
stability: "experimental"
```

---

## Prompt Template Format

### System Prompt (`system.txt`)

```
You are an expert Diamond programming language assistant. Diamond is an 
agent-native language with algebraic effects, capability-based security, 
and semantic typing.

Key Diamond principles you must follow:
1. All external operations require explicit capabilities via `import ... requires { ... }`
2. Side effects use algebraic effects with `perform` and handlers
3. Generics use square brackets: `fn identity[T](x: T) -> T`
4. The Diamond operator `<>` enables structured probabilistic branching
5. Semantic types with refinements enforce data validity

When generating code:
- Always include capability imports for I/O, network, or system operations
- Use `perform` for effect operations, never assume ambient authority
- Include doc comments with examples
- Handle errors explicitly with Result types
- Follow the formatting conventions (2-space indent, trailing commas)

{additional_context}
```

### User Template (`user_template.txt`)

```
Generate Diamond code for the following task:

## Task Description
{task_description}

## Required Capabilities
{capabilities}

## Expected Behavior
{expected_behavior}

## Additional Context
{context}

Please provide:
1. The Diamond code implementation
2. Brief explanation of design decisions
3. Example usage (if not included inline)
4. Any security considerations
```

---

## Example Structure

Each prompt pack includes few-shot examples:

```
examples/
├── example1/
│   ├── input.txt           # The user's request
│   ├── output.dm           # Expected Diamond code output
│   └── explanation.txt     # Why this output is correct
├── example2/
│   ├── input.txt
│   ├── output.dm
│   └── explanation.txt
└── ...
```

### Example Input (`examples/example1/input.txt`)

```
Create a function that fetches user data from an API and caches the result.
The cache should expire after 5 minutes.
```

### Example Output (`examples/example1/output.dm`)

```diamond
import std/net requires { Network }
import std/time requires { Time }
import std/memory

/// A cached user data fetcher with TTL-based expiration.
///
/// # Example
/// ```diamond
/// let user = fetch_user_cached("user-123")?
/// ```
///
/// @capability Network(read)
/// @capability Time(read)
fn fetch_user_cached(
    user_id: String,
    cache: Cache[String, User],
) -> Result[User, FetchError] performs Network, Time {
    let cache_key = "user:" + user_id
    
    // Check cache first
    match cache.get(cache_key) {
        Some(entry) if !entry.is_expired(Duration.minutes(5)) => {
            Ok(entry.value)
        }
        _ => {
            // Fetch from API
            let response = perform Network.fetch(
                "https://api.example.com/users/" + user_id
            )?
            
            let user = parse_user(response.body)?
            
            // Cache the result
            cache.put(cache_key, CacheEntry {
                value: user,
                cached_at: perform Time.now(),
            })
            
            Ok(user)
        }
    }
}
```

---

## Safety Constraints

### No Capability Escalation
Generated code must not request more capabilities than specified:

```yaml
# metadata.yaml safety rule
safety:
  - "no_capability_escalation"
```

**Enforcement:**
- Parse generated imports for capability declarations
- Compare against allowed capabilities in metadata
- Fail validation if unexpected capabilities present

### No Ambient Authority
Generated code must not assume access without explicit grants:

```diamond
// WRONG: Assumes file access
fn read_config() -> Config {
    let content = fs.read("config.toml")  // No capability!
}

// RIGHT: Explicit capability requirement
import std/fs requires { FileSystem(read) }

fn read_config() -> Config performs FileSystem {
    perform FileSystem.read("config.toml")
}
```

### Input Validation Required
User-provided input must be validated before use:

```diamond
// Generated code should include validation
fn process_user_input(input: String) -> Result[Output, ValidationError] {
    // Validate input first
    let validated = validate_input(input)?
    
    // Process validated input
    process(validated)
}
```

---

## Testing Prompt Packs

### Test Case Format

```yaml
# tests/test_cases.yaml
test_cases:
  - name: "simple_function_generation"
    input: "Create a function that adds two numbers"
    expected_patterns:
      - "fn add"
      - "-> Int"
    forbidden_patterns:
      - "import std/fs"  # Should not need filesystem
    capabilities_expected: []
    
  - name: "api_fetch_with_capabilities"
    input: "Fetch data from an external API"
    expected_patterns:
      - "import std/net requires"
      - "perform Network"
    capabilities_expected:
      - "Network"
```

### Validation Script

```bash
# Run prompt pack validation
python scripts/validate_prompts.py --pack code-generation

# Test against specific model
python scripts/test_prompts.py --pack code-generation --model gpt-4

# Validate all packs
python scripts/validate_prompts.py --all
```

---

## Quality Metrics

Track prompt pack effectiveness:

| Metric | Description | Target |
| --- | --- | --- |
| Compile Rate | % of generated code that compiles | > 90% |
| Type-Check Rate | % that passes type checking | > 85% |
| Capability Compliance | % with correct capabilities | > 95% |
| Safety Compliance | % passing safety constraints | 100% |
| User Satisfaction | Rating from user feedback | > 4.0/5.0 |

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the new prompt pack.
   - Identify target use cases and models.
   - Define safety constraints and quality expectations.

2. **Development**
   - Create directory structure following the template.
   - Write system and user prompt templates.
   - Add few-shot examples (minimum 3).
   - Define test cases.

3. **Testing**
   - Run validation against target models.
   - Verify safety constraints are enforced.
   - Collect quality metrics.
   - Iterate on prompts based on results.

4. **Review**
   - Request review from ML Enablement WG.
   - Verify capability and safety compliance.
   - Check documentation completeness.

5. **Publication**
   - Add to index.yaml.
   - Update README with pack description.
   - Announce in release notes.

---

## Quality Checklist (Pre-Merge)

- [ ] Metadata.yaml is complete and valid.
- [ ] System prompt references Diamond principles correctly.
- [ ] User template has clear placeholders.
- [ ] At least 3 few-shot examples provided.
- [ ] Test cases cover success and failure scenarios.
- [ ] Safety constraints are defined and tested.
- [ ] Capability requirements are accurate.
- [ ] Validation passes against primary models.
- [ ] README documents usage and limitations.
- [ ] No secrets or sensitive data in examples.

---

## Versioning

Prompt packs follow semantic versioning:

- **Major**: Breaking changes to prompt format or behavior.
- **Minor**: New capabilities, improved quality.
- **Patch**: Bug fixes, example updates.

Track versions in metadata.yaml and maintain changelog per pack.

---

## Future Enhancements

- A/B testing framework for prompt variations.
- Automatic prompt optimization using feedback.
- Model-specific prompt tuning.
- Integration with IDE for inline assistance.
- Prompt chaining for complex multi-step tasks.
- Evaluation harness with synthetic test suites.
- Community prompt pack contributions.

---

Prompt packs are Diamond's interface to AI assistance. Well-crafted prompts ensure that LLMs produce code that is idiomatic, secure, and capability-aware. Every prompt template should embody Diamond's principles while being practically useful for developers.