# Diamond (<>) Algebraic Effects Specification

**Status:** Draft v0.1  
**Audience:** Language/runtime designers, compiler engineers, runtime implementers, and tooling authors.

---

## 1. Purpose

Algebraic effects provide Diamond with a unified abstraction for suspending, resuming, and supervising probabilistic agent computations. Effects enable deterministic surfaces for operations that may involve external services (LLMs, tools, networks) or long-lived workflows by separating **effect invocation** from **effect handling**.

---

## 2. Design Goals

1. **Suspension and Resumption** — Any effect may capture the current continuation, serialize it, and resume later.
2. **Deterministic Interfaces** — Effect signatures describe input/output types and effectful behavior explicitly.
3. **Composability** — Effects compose via handlers; handlers may intercept, transform, retry, or escalate operations.
4. **Capability Safety** — Effect execution is bound by capabilities (object-capability security); handlers operate within explicit authority.
5. **LLM Ergonomics** — Syntax is minimal yet explicit (`perform`, `handle`) to align with agent cognition patterns.

---

## 3. Effect Definitions

Effects are declared at the top level:

```
effect AskUser(question: String) -> String
effect ToolCall(name: String, payload: Json) -> ToolResult
effect Wait(duration: Duration)
effect Supervisor(context: FailureContext) -> SupervisorAction
```

### 3.1 Syntax

```
EffectDeclaration ::= 'effect' IDENTIFIER EffectSignatureList

EffectSignatureList ::= 
    FunctionSignature
  | INDENT { FunctionSignature } DEDENT

FunctionSignature ::= IDENTIFIER '(' ParameterList? ')' [ '->' TypeExpr ]
```

- Multiple signatures support overloading; each function represents a distinct operation within the effect namespace.
- All effect operations implicitly return `()` (Unit) if no return type is specified.

---

## 4. Performing Effects

### 4.1 `perform` Keyword

```
result = perform AskUser("What is your name?")
perform Wait(Duration.hours(24))
```

- `perform` suspends the current computation until a handler provides a response or propagates control.
- The expression evaluates to the handler’s return value (e.g., `String` for `AskUser`).

### 4.2 Syntactic Sugar

High-level constructs desugar to `perform`:

- `prompt` definitions invoke `perform Prompt.Run(...)`.
- Semantic casts (e.g., `value as SemanticType`) trigger `perform Cast(...)`.
- The Diamond operator `< >` may internally `perform Decision(...)`.

---

## 5. Handling Effects

### 5.1 `handle` Blocks

```
handle workflow() with:
    case AskUser(q, resume):
        notify_user(q)
        scheduler.persist(resume)
        suspend()

    case Wait(d, resume):
        scheduler.sleep(d, resume)

    case ToolCall(name, payload, resume):
        with tools[name] as tool:
            resume(tool.execute(payload))
```

- Each `case` receives the effect arguments plus an automatically injected continuation parameter (`resume`).
- Handlers may call `resume(value)` zero or more times:
  - **Single resume:** standard continuation semantics.
  - **Multiple resumption:** allows replay or retry strategies when semantics permit (must be explicitly enabled per effect).
- Handlers can decline to resume (e.g., escalate) by not invoking `resume`.

### 5.2 Handler Scope

- Handlers apply to the lexical body of `handle`.
- Nested handlers override outer ones for matching effects.
- Unhandled effects propagate outward (similar to exception propagation). If no handler is found, the runtime applies default policies (typically failing the agent).

---

## 6. Continuation Model

### 6.1 Continuation Object

- `resume` encapsulates the suspended computation and captured environment.
- Continuations are **single-use** by default. Multi-use must be declared via `effect` metadata (`@reentrant`).
- Continuation serialization is handled by the runtime:
  - Encoded as opaque, signed payloads.
  - Includes metadata: effect name, checksum, creation timestamp, effect payload fingerprint.

### 6.2 Persistence & Resumption

1. Handler decides to suspend and persists the continuation via runtime APIs.
2. Runtime stores the payload in the continuation store (hot cache + durable store).
3. Upon resumption trigger (user reply, scheduled wake), runtime retrieves and validates the payload, then calls `resume(value)`.

### 6.3 Invalid Continuations

- Expired or tampered continuations must be rejected.
- Runtime notifies supervisors via `perform Supervisor(...)`.

---

## 7. Effect Typing

### 7.1 Effect Signatures

- An effect signature `Effect Op(args) -> Return` contributes an effect token `Effect.Op` to the effect environment.
- Functions performing `Effect` automatically list it in their effect set (`! { Effect }` seen in tooling).

### 7.2 Handler Typing Rules

- Handlers must accept arguments matching the effect signature plus `resume`.
- `resume` is typed as `(Return) -> ContinuationResult`, where `ContinuationResult` equals the surrounding computation’s expected type.
- Handler body type equals the handled expression’s type.

### 7.3 Effect Discharge

- When a handler consumes an effect (i.e., fully resolves it without re-performing), the outer effect set excludes that effect.
- Re-throwing an effect (`perform` inside handler) reintroduces it to the caller’s effect set.

---

## 8. Runtime Semantics

### 8.1 Effect Dispatch

1. `perform` emits an effect invocation record containing:
   - Effect namespace & operation.
   - Arguments (serialized).
   - Current capability context & security metadata.
2. Runtime walks stack of active handlers:
   - Lexical handlers (static) resolved at compile time.
   - Dynamic handlers stored in runtime stack frames.
3. If handler found, control transfers to handler with continuation.
4. If no handler, runtime invokes supervisor policy (default: escalate or fail).

### 8.2 Serialized Format

- Runtime uses a canonical CBOR/JSON representation for effect payloads plus `resume` tokens.
- Continuations carry:
  - `continuation_id`
  - `effect_signature`
  - `serialized_environment` (Wasm linear memory snapshots or structured capture)
  - `capability_manifest_hash`

### 8.3 Determinism Constraints

- Handler logic must not rely on non-deterministic global state unless via explicit capabilities.
- Resumed computations must see the same environment or fail gracefully (no partial state corruption).

---

## 9. Standard Effects

| Effect       | Purpose                                               | Typical Handlers                       |
|--------------|-------------------------------------------------------|-----------------------------------------|
| `AskUser`    | Request human input                                   | Supervisor service, UI callback         |
| `ToolCall`   | Execute an external tool/API                          | Tool dispatcher, caching layer          |
| `Wait`       | Delay execution until time/event                      | Scheduler, timer service                |
| `Prompt.Run` | Perform an LLM inference                              | Prompt router, rate limiter, cache      |
| `Decision`   | Execute `< >` branching / constrained selection       | Decision engine, fallback heuristics    |
| `Persist`    | Save mutable state snapshots                          | Storage engine, transactional log       |
| `Supervisor` | Escalation for unhandled failures or policy decisions | Human-in-the-loop, safety agent         |

Effects may declare metadata:

```
effect ToolCall(name: String, payload: Json) -> ToolResult:
    @requires Capability.Tool
    @reentrant false
    @timeout Duration.seconds(30)
```

---

## 10. Capability Integration

- Each effect operation specifies required capabilities; compiler ensures handlers possess them.
- `perform` inherits the caller’s capability context; handlers may attenuate or extend context locally.
- Continuations store capability manifests; resumption fails if required capabilities are unavailable.

---

## 11. Error Handling & Supervision

- If a handler throws an error or declines to resume, runtime emits `perform Supervisor(FailureContext)`:
  - Contains stack trace, effect payload, capability context, and suggested remediation.
- Supervisors may retry, replace arguments, or terminate the agent.
- Unrecoverable failures bubble to the host (with signed diagnostics).

---

## 12. Testing & Deterministic Mode

- Runtime provides a deterministic harness where effect handlers are replaced by mocks.
- Continuations can be inspected in test mode (human-readable representation) for verification.
- Tooling supports effect tracing: developers can visualize `perform`/`handle` sequences.

---

## 13. Future Extensions & Open Questions

1. **Effect Polymorphism:** Allow generic functions to abstract over effect sets (`forall E. func f() ! E`).
2. **Multi-shot Continuations:** Formalize patterns for repeating `resume`.
3. **Effect Prioritization:** Scheduling strategies when multiple pending continuations exist.
4. **Distributed Continuations:** Resume across distributed runtimes with cryptographic verification.
5. **Static Capability Inference:** Auto-derive required capabilities from effect usage.

Modifications to this specification require an RFC referencing prior decisions in `docs/design-decisions/`.

---