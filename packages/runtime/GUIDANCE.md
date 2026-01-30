# Runtime Package Guidance

## Purpose
The `packages/runtime/` workspace contains the Diamond execution runtime—the engine that brings compiled Diamond agents to life. This package implements the capability manager, effect dispatcher, continuation storage, and host bindings that enable secure, resumable, long-lived agent workflows. All components must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, zero-trust WebAssembly execution, tiered continuation storage.
- **`diamond3.md`** — Algebraic effects, resumable handlers, and module-level capability injection.

The runtime is where Diamond's security promises are enforced and its durability guarantees are realized.

---

## Directory Contract

| Path | Owner Working Groups | Scope & Expectations |
| --- | --- | --- |
| `continuations/` | Runtime | Continuation capture, serialization, tiered storage (hot/warm/cold). |
| `effects/` | Runtime + Language | Effect dispatcher, handler registration, resume mechanics. |
| `host/` | Runtime + Security | Capability manager, sandbox enforcement, host bindings, telemetry. |
| `README.md` | All WGs | Architecture overview, build instructions, integration guide. |
| `GUIDANCE.md` | All WGs | This file—contribution and quality standards. |
| `Cargo.toml` | Runtime | Workspace manifest for runtime crates. |

Subdirectories must not be created without an owning working group, README, and guidance note.

---

## Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │           Diamond Agent                 │
                    │         (Wasm Component)                │
                    └──────────────┬──────────────────────────┘
                                   │ perform effects
                    ┌──────────────▼──────────────────────────┐
                    │        Effect Dispatcher                │
                    │   (routes effects to handlers)          │
                    └────┬─────────────┬─────────────┬────────┘
                         │             │             │
            ┌────────────▼──┐  ┌───────▼──────┐  ┌──▼────────────┐
            │  Host Effects │  │ Agent Effects│  │User Handlers  │
            │  (I/O, Net)   │  │ (LLM, Tools) │  │(Custom Logic) │
            └───────────────┘  └──────────────┘  └───────────────┘
                         │
            ┌────────────▼────────────────────────────────────┐
            │            Capability Manager                   │
            │   (validates authority for each operation)      │
            └────────────┬────────────────────────────────────┘
                         │
            ┌────────────▼────────────────────────────────────┐
            │          Continuation Store                     │
            │   (hot/warm/cold tiered persistence)            │
            └─────────────────────────────────────────────────┘
```

---

## Core Subsystems

### Continuation Store (`continuations/`)
Manages the lifecycle of suspended computations:

1. **Capture**: Serialize execution state when `perform` suspends.
2. **Storage Tiers**:
   - **Hot**: In-memory, sub-millisecond resume latency.
   - **Warm**: Local disk or Redis, millisecond-scale resume.
   - **Cold**: Durable storage (S3, database), second-scale resume.
3. **Resume**: Deserialize and restore execution from any tier.
4. **Garbage Collection**: Reclaim completed or expired continuations.

### Effect Dispatcher (`effects/`)
Routes algebraic effects to appropriate handlers:

1. **Effect Registration**: Handlers register for specific effect types.
2. **Dispatch**: Match `perform` operations to registered handlers.
3. **Resume Coordination**: Pass values back to suspended computations.
4. **Effect Composition**: Support handler stacking and delegation.
5. **Builtin Effects**: Provide core effects (I/O, time, randomness).

### Host Bindings (`host/`)
Interfaces between Diamond runtime and host environment:

1. **Capability Manager**: Validate authority before operations.
2. **Sandbox Enforcement**: Isolate agents via Wasm boundaries.
3. **Resource Limits**: CPU, memory, time quotas per agent.
4. **Telemetry**: Emit traces, metrics, and logs.
5. **Host Functions**: Provide platform-specific implementations.

---

## Security Model

### Object-Capability Enforcement
Every operation requiring authority must:

1. **Receive Capability**: Obtain explicit capability grant.
2. **Validate at Boundary**: Runtime checks capability before execution.
3. **Attenuate on Delegation**: Reduce permissions when passing to sub-agents.
4. **Audit Trail**: Log all capability exercises for review.

### Sandbox Guarantees
- Agents cannot access host resources without explicit grants.
- Memory isolation via Wasm linear memory.
- No ambient authority—all capabilities are explicit.
- Capability manifests are cryptographically bound to code.

### Threat Mitigations
| Threat | Mitigation |
| --- | --- |
| Capability escalation | Static validation + runtime checks |
| Continuation tampering | Cryptographic integrity verification |
| Resource exhaustion | Configurable quotas with enforcement |
| Effect handler bypass | Type-safe dispatch with sealed handlers |
| Host escape | Wasm sandbox with capability-gated host functions |

---

## Continuation Persistence

### Serialization Format
Continuations must be:
- **Deterministic**: Same state produces identical bytes.
- **Versioned**: Include format version for migration.
- **Compact**: Minimize storage footprint.
- **Integrity-Protected**: Include cryptographic hash.

### Storage Interface
```rust
#[async_trait]
pub trait ContinuationStore {
    /// Save a continuation, returning its identifier.
    async fn save(&self, cont: &Continuation) -> Result<ContinuationId>;
    
    /// Load a continuation by identifier.
    async fn load(&self, id: ContinuationId) -> Result<Continuation>;
    
    /// Delete a continuation (after completion or expiry).
    async fn delete(&self, id: ContinuationId) -> Result<()>;
    
    /// Promote continuation to hotter tier.
    async fn promote(&self, id: ContinuationId, tier: StorageTier) -> Result<()>;
    
    /// Demote continuation to colder tier.
    async fn demote(&self, id: ContinuationId, tier: StorageTier) -> Result<()>;
}
```

### Tier Configuration
```toml
[continuations]
hot_capacity_mb = 512
hot_ttl_seconds = 300
warm_backend = "redis"
warm_ttl_seconds = 3600
cold_backend = "s3"
cold_bucket = "diamond-continuations"
```

---

## Effect System Implementation

### Handler Registration
```rust
pub trait EffectHandler: Send + Sync {
    /// Handle an effect operation, optionally resuming the continuation.
    fn handle(&self, 
              op: &EffectOp, 
              resume: ResumeFn) -> Result<HandleResult>;
    
    /// Declare which effects this handler covers.
    fn handles(&self) -> &[EffectId];
}
```

### Builtin Effects
| Effect | Operations | Capability Required |
| --- | --- | --- |
| `Console` | `print`, `read_line` | `Console` |
| `FileSystem` | `read`, `write`, `delete` | `FileSystem` |
| `Network` | `fetch`, `listen`, `connect` | `Network` |
| `Time` | `now`, `sleep` | `Time` |
| `Random` | `random_bytes`, `random_int` | `Random` |
| `LLM` | `complete`, `embed`, `classify` | `LLM` |

### Effect Execution Flow
1. Agent performs effect via `perform EffectType.operation(args)`.
2. Dispatcher captures current continuation.
3. Handler receives operation and resume function.
4. Handler executes operation (may be async).
5. Handler calls `resume(result)` to continue agent.
6. Agent receives result and continues execution.

---

## Coding Standards

1. **Async Runtime**
   - Use `tokio` as the default async runtime.
   - Support `async-std` behind a feature flag.
   - Avoid blocking operations on async threads.

2. **Error Handling**
   - Use `thiserror` for error types.
   - Provide rich context for runtime errors.
   - Distinguish recoverable vs. fatal errors.
   - Include continuation IDs in error context.

3. **Safety**
   - Use `#![forbid(unsafe_code)]` where possible.
   - Document and audit any `unsafe` blocks.
   - Prefer safe abstractions over raw pointers.

4. **Testing**
   - Unit tests for all public functions.
   - Integration tests with mock Wasm agents.
   - Fuzz tests for continuation serialization.
   - Stress tests for concurrent effect handling.

5. **Telemetry**
   - Use `tracing` for structured logging.
   - Emit OpenTelemetry-compatible spans and metrics.
   - Include correlation IDs across effect boundaries.
   - Provide hooks for custom telemetry backends.

---

## Development Workflow

### Prerequisites
- Rust toolchain (stable, pinned in `rust-toolchain.toml`).
- `wasmtime` for Wasm execution.
- Redis (optional, for warm continuation tier testing).
- Docker (optional, for integration tests).

### Common Commands
```bash
# Build runtime crates
cargo build --workspace

# Run tests
cargo test --workspace

# Run with specific features
cargo test --features async-std-runtime

# Benchmark continuation operations
cargo bench -p diamond-continuations

# Generate documentation
cargo doc --workspace --no-deps --open
```

---

## Integration Patterns

### Embedding the Runtime
```rust
use diamond_runtime::{Runtime, Config, CapabilitySet};

let config = Config::builder()
    .with_continuation_store(redis_store)
    .with_capability_manager(custom_manager)
    .with_telemetry(otel_exporter)
    .build();

let runtime = Runtime::new(config)?;

// Load compiled agent
let agent = runtime.load_component(wasm_bytes)?;

// Grant capabilities
let caps = CapabilitySet::new()
    .with(Capability::Network)
    .with(Capability::LLM);

// Execute with capabilities
let result = runtime.execute(agent, caps).await?;
```

### Custom Effect Handlers
```rust
struct MyDatabaseHandler { pool: DbPool }

impl EffectHandler for MyDatabaseHandler {
    fn handle(&self, op: &EffectOp, resume: ResumeFn) -> Result<HandleResult> {
        match op.name.as_str() {
            "query" => {
                let sql = op.args.get::<String>("sql")?;
                let rows = self.pool.query(&sql)?;
                resume.call(rows.into())
            }
            _ => Err(EffectError::UnhandledOperation)
        }
    }
    
    fn handles(&self) -> &[EffectId] {
        &[EffectId::from("Database")]
    }
}
```

---

## Review & Approval Matrix

| Change Type | Required Approvals |
| --- | --- |
| Capability enforcement changes | Runtime WG + Security WG |
| Continuation format changes | Runtime WG + RFC |
| Effect dispatch modifications | Runtime WG + Language WG |
| Host binding additions | Runtime WG + Security WG |
| Performance optimizations | Runtime WG + benchmarks |
| Telemetry changes | Runtime WG + DX WG |

---

## Quality Checklist (Pre-Merge)

- [ ] Code follows `rustfmt` and passes `clippy` without warnings.
- [ ] All public APIs are documented with examples.
- [ ] Capability checks are present for all sensitive operations.
- [ ] Continuation serialization is deterministic and versioned.
- [ ] Effect handlers are tested for both success and failure paths.
- [ ] Telemetry spans cover critical operations.
- [ ] No panics in library code; all errors use `Result`.
- [ ] Performance benchmarks show no unexpected regressions.
- [ ] Security implications documented for new features.
- [ ] README and CHANGELOG updated as needed.

---

## Future Enhancements

- Distributed continuation storage with consistent hashing.
- Effect handler hot-reloading for zero-downtime updates.
- Multi-tenant runtime with per-tenant resource quotas.
- Hardware security module integration for capability signing.
- WebAssembly GC support for improved memory management.
- Checkpoint/restore for long-running agent workflows.
- Speculation support for optimistic effect execution.

---

The runtime is Diamond's foundation for secure, durable agent execution. Every capability check, every continuation save, every effect dispatch must uphold the language's promises. Build with security-first thinking and operational excellence in mind.