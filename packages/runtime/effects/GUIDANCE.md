# Effects Subsystem Guidance

## Purpose
The `packages/runtime/effects/` directory implements the algebraic effect system that powers Diamond's resumable, composable side-effect handling. This subsystem dispatches effect operations to handlers, manages resumption of suspended computations, and enforces capability requirements for effectful operations. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, capability discipline, and structured agent workflows.
- **`diamond2.md`** — Architectural feasibility, zero-trust execution, and durable computation guarantees.
- **`diamond3.md`** — Algebraic effects, `perform`/`handler` semantics, and resumable continuations.

The effect system is central to Diamond's promise: enabling agents to perform side effects in a controlled, auditable, and resumable manner.

---

## Directory Contract

| Path | Purpose |
| --- | --- |
| `mod.rs` | Public API exports, effect system initialization. |
| `dispatcher.rs` | Effect dispatch logic, handler routing, resume coordination. |
| `handler.rs` | Handler trait definitions, registration, and lifecycle. |
| `operations.rs` | Effect operation types, argument encoding, result handling. |
| `builtins/` | Built-in effect implementations (Console, FileSystem, Network, etc.). |
| `resume.rs` | Resume function implementation, continuation handoff. |
| `composition.rs` | Handler stacking, delegation, and effect transformation. |
| `README.md` | Subsystem overview, API documentation, usage examples. |
| `GUIDANCE.md` | This file—contribution and quality standards. |

---

## Core Concepts

### Algebraic Effects
Diamond's effect system follows the algebraic effects paradigm:

1. **Effect Declaration**: Effects declare a set of operations with typed signatures.
2. **Perform**: Code requests an operation via `perform Effect.operation(args)`.
3. **Handler**: A handler intercepts the operation and decides how to process it.
4. **Resume**: The handler can resume the suspended computation with a result.

### Effect Flow
```
Agent Code                     Effect Dispatcher                 Handler
    │                                │                              │
    │ perform Console.print("hi")    │                              │
    │ ─────────────────────────────► │                              │
    │                                │  dispatch(Console, print)    │
    │                                │ ────────────────────────────►│
    │                                │                              │
    │                                │      (handler executes)      │
    │                                │                              │
    │                                │  resume(())                  │
    │                                │ ◄────────────────────────────│
    │ ◄───────────────────────────── │                              │
    │ (continues with result)        │                              │
```

---

## API Design

### Effect Operations

```rust
/// Represents an effect operation to be performed.
#[derive(Debug, Clone)]
pub struct EffectOp {
    /// The effect type identifier.
    pub effect_id: EffectId,
    /// The operation name within the effect.
    pub operation: String,
    /// Typed arguments for the operation.
    pub args: EffectArgs,
    /// Source location for diagnostics.
    pub source_span: Option<SourceSpan>,
    /// Required capability for this operation.
    pub required_capability: Option<CapabilityId>,
}

/// Typed argument container for effect operations.
pub struct EffectArgs {
    inner: HashMap<String, EffectValue>,
}

impl EffectArgs {
    pub fn get<T: FromEffectValue>(&self, key: &str) -> Result<T, EffectError>;
    pub fn set<T: IntoEffectValue>(&mut self, key: &str, value: T);
}
```

### Handler Trait

```rust
/// Trait for effect handlers.
#[async_trait]
pub trait EffectHandler: Send + Sync {
    /// Handle an effect operation.
    /// 
    /// # Arguments
    /// * `op` - The effect operation being performed.
    /// * `resume` - Function to resume the suspended computation.
    /// * `ctx` - Handler context with capabilities and telemetry.
    /// 
    /// # Returns
    /// * `HandleResult::Resumed` - Computation was resumed with a value.
    /// * `HandleResult::Suspended` - Computation suspended for async handling.
    /// * `HandleResult::Delegated` - Operation delegated to outer handler.
    /// * `HandleResult::Failed` - Operation failed with error.
    async fn handle(
        &self,
        op: &EffectOp,
        resume: ResumeFn,
        ctx: &HandlerContext,
    ) -> Result<HandleResult, EffectError>;
    
    /// Declare which effect types this handler covers.
    fn handles(&self) -> &[EffectId];
    
    /// Priority for handler ordering (higher = checked first).
    fn priority(&self) -> i32 { 0 }
    
    /// Whether this handler supports resumable operations.
    fn is_resumable(&self) -> bool { true }
}
```

### Effect Dispatcher

```rust
/// Central dispatcher for routing effects to handlers.
pub struct EffectDispatcher {
    handlers: Vec<Box<dyn EffectHandler>>,
    capability_manager: Arc<CapabilityManager>,
    telemetry: Arc<dyn TelemetryProvider>,
}

impl EffectDispatcher {
    /// Register a new effect handler.
    pub fn register(&mut self, handler: Box<dyn EffectHandler>);
    
    /// Unregister a handler by effect ID.
    pub fn unregister(&mut self, effect_id: &EffectId);
    
    /// Dispatch an effect operation to the appropriate handler.
    pub async fn dispatch(
        &self,
        op: EffectOp,
        continuation: Continuation,
    ) -> Result<DispatchResult, EffectError>;
    
    /// Check if an effect type has a registered handler.
    pub fn has_handler(&self, effect_id: &EffectId) -> bool;
}
```

### Resume Function

```rust
/// Function type for resuming suspended computations.
pub struct ResumeFn {
    continuation_id: ContinuationId,
    store: Arc<dyn ContinuationStore>,
}

impl ResumeFn {
    /// Resume the computation with the given result value.
    pub async fn call<T: IntoEffectValue>(self, value: T) -> Result<(), EffectError>;
    
    /// Resume the computation with an error.
    pub async fn fail(self, error: EffectError) -> Result<(), EffectError>;
    
    /// Get the continuation ID for persistence.
    pub fn continuation_id(&self) -> ContinuationId;
}
```

---

## Built-in Effects

### Console Effect
```rust
pub struct ConsoleHandler {
    stdin: Arc<dyn Read + Send + Sync>,
    stdout: Arc<dyn Write + Send + Sync>,
    stderr: Arc<dyn Write + Send + Sync>,
}

// Operations:
// - print(message: String) -> ()
// - read_line() -> String
// - error(message: String) -> ()
```

### FileSystem Effect
```rust
pub struct FileSystemHandler {
    root: PathBuf,
    capability: FileSystemCapability,
}

// Operations:
// - read(path: String) -> Bytes
// - write(path: String, content: Bytes) -> ()
// - delete(path: String) -> ()
// - list(path: String) -> Vec<String>
// - exists(path: String) -> Bool
```

### Network Effect
```rust
pub struct NetworkHandler {
    client: HttpClient,
    capability: NetworkCapability,
}

// Operations:
// - fetch(url: String, options: FetchOptions) -> Response
// - connect(addr: String) -> Connection
// - listen(addr: String) -> Listener
```

### Time Effect
```rust
pub struct TimeHandler;

// Operations:
// - now() -> Timestamp
// - sleep(duration: Duration) -> ()
```

### Random Effect
```rust
pub struct RandomHandler {
    rng: Arc<Mutex<StdRng>>,
}

// Operations:
// - random_bytes(count: usize) -> Bytes
// - random_int(min: i64, max: i64) -> i64
// - random_float() -> f64
```

### LLM Effect
```rust
pub struct LlmHandler {
    provider: Arc<dyn LlmProvider>,
    capability: LlmCapability,
}

// Operations:
// - complete(prompt: String, options: CompletionOptions) -> String
// - embed(text: String) -> Vec<f32>
// - classify(text: String, labels: Vec<String>) -> String
```

---

## Handler Composition

### Handler Stacking
Handlers can be stacked to provide layered functionality:

```rust
// Outer handler wraps inner handler
let stacked = handler1.stack(handler2);

// When effect is performed:
// 1. handler1.handle() called first
// 2. If HandleResult::Delegated, handler2.handle() called
// 3. Result bubbles back up
```

### Effect Transformation
Transform effects from one type to another:

```rust
pub trait EffectTransformer: Send + Sync {
    fn transform(&self, op: EffectOp) -> Result<EffectOp, EffectError>;
}

// Example: Transform Database effect to FileSystem effect for testing
let mock_db = MockDatabaseTransformer::new(file_system_handler);
```

### Handler Context
```rust
pub struct HandlerContext {
    /// Available capabilities for this handler.
    pub capabilities: CapabilitySet,
    /// Telemetry span for tracing.
    pub span: tracing::Span,
    /// Agent identity performing the effect.
    pub agent_id: AgentId,
    /// Request correlation ID.
    pub correlation_id: CorrelationId,
}
```

---

## Capability Integration

Every effectful operation may require capabilities:

```rust
impl EffectDispatcher {
    async fn dispatch(&self, op: EffectOp, cont: Continuation) -> Result<DispatchResult, EffectError> {
        // 1. Check capability requirement
        if let Some(cap) = &op.required_capability {
            self.capability_manager.validate(cap, &cont.capabilities)?;
        }
        
        // 2. Find and invoke handler
        let handler = self.find_handler(&op.effect_id)?;
        
        // 3. Execute with telemetry
        let span = tracing::info_span!("effect", 
            effect = %op.effect_id,
            operation = %op.operation,
        );
        
        handler.handle(&op, resume_fn, &ctx).instrument(span).await
    }
}
```

---

## Error Handling

### Error Types
```rust
#[derive(Debug, Error)]
pub enum EffectError {
    #[error("no handler registered for effect: {0}")]
    UnhandledEffect(EffectId),
    
    #[error("operation not supported: {effect}.{operation}")]
    UnsupportedOperation { effect: EffectId, operation: String },
    
    #[error("capability denied: {0}")]
    CapabilityDenied(CapabilityId),
    
    #[error("handler failed: {0}")]
    HandlerFailed(String),
    
    #[error("resume failed: continuation {0} not found")]
    ResumeFailed(ContinuationId),
    
    #[error("argument error: {0}")]
    ArgumentError(String),
    
    #[error("timeout: operation exceeded {0:?}")]
    Timeout(Duration),
}
```

### Error Recovery
- Handlers should return `Err(EffectError)` for recoverable errors.
- Fatal errors should propagate to the runtime for agent termination.
- Effect errors include context for debugging (operation, arguments, handler).

---

## Testing Strategy

### Unit Tests
- Test individual handlers in isolation.
- Mock continuation stores and capability managers.
- Verify correct operation dispatch.

### Handler Tests
```rust
#[tokio::test]
async fn test_console_print() {
    let mut output = Vec::new();
    let handler = ConsoleHandler::new(
        std::io::empty(),
        &mut output,
        std::io::sink(),
    );
    
    let op = EffectOp::new("Console", "print")
        .with_arg("message", "Hello");
    
    let (resume, receiver) = mock_resume();
    handler.handle(&op, resume, &ctx()).await.unwrap();
    
    assert_eq!(output, b"Hello");
    assert!(receiver.was_resumed_with(()));
}
```

### Integration Tests
- Test handler stacking and delegation.
- Verify capability enforcement.
- Test async resume scenarios.

### Fuzz Tests
- Fuzz effect argument parsing.
- Fuzz handler dispatch with random operations.

---

## Performance Considerations

1. **Handler Lookup**: Use hash map for O(1) handler lookup by effect ID.
2. **Argument Parsing**: Lazy deserialization of effect arguments.
3. **Resume Path**: Minimize allocations in the resume hot path.
4. **Telemetry**: Make telemetry collection zero-cost when disabled.

### Benchmarks
```rust
#[bench]
fn bench_effect_dispatch(b: &mut Bencher) {
    let dispatcher = setup_dispatcher();
    let op = simple_effect_op();
    
    b.iter(|| {
        dispatcher.dispatch(op.clone(), mock_continuation()).await
    });
}
```

---

## Coding Standards

1. **Async Safety**: All handlers must be `Send + Sync`.
2. **No Blocking**: Never block in async handlers; use `spawn_blocking` if needed.
3. **Timeout Support**: Long-running operations must respect timeout configuration.
4. **Telemetry**: Emit spans for all effect operations.
5. **Documentation**: Document capability requirements for all operations.

---

## Quality Checklist (Pre-Merge)

- [ ] Handler implements all declared operations.
- [ ] Capability requirements documented and enforced.
- [ ] Resume and fail paths tested.
- [ ] Error messages include sufficient context.
- [ ] Telemetry spans cover operation lifecycle.
- [ ] No blocking operations on async threads.
- [ ] Handler priority documented if non-default.
- [ ] Integration with continuation store tested.
- [ ] Performance benchmarks added for new handlers.
- [ ] README updated with new effect operations.

---

## Future Enhancements

- Effect polymorphism for generic handlers.
- Effect inference optimization at compile time.
- Speculative effect execution with rollback.
- Effect operation batching for performance.
- Cross-agent effect delegation.
- Effect replay for debugging and testing.

---

The effect system is Diamond's mechanism for controlled interaction with the world. Every perform, every handler, every resume must be correct, auditable, and secure. Build handlers that are robust, well-documented, and respect the capability boundaries that make Diamond agents trustworthy.