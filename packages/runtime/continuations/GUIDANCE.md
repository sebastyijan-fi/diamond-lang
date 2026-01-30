# Continuations Subsystem Guidance

## Purpose
The `packages/runtime/continuations/` directory implements Diamond's resumable continuation system—the mechanism that enables long-lived, durable agent workflows. This subsystem captures, serializes, stores, and resumes suspended computations across effect boundaries. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Tiered continuation storage (hot/warm/cold), durability guarantees, and architectural feasibility.
- **`diamond3.md`** — Algebraic effects, resumable handlers, and continuation semantics.

Continuations are the heart of Diamond's durability promise—enabling agents to suspend indefinitely and resume exactly where they left off.

---

## Directory Contract

| Path | Scope & Expectations |
| --- | --- |
| `lib.rs` | Crate root, public API exports for continuation operations. |
| `capture.rs` | Continuation capture logic—extracting execution state at suspend points. |
| `serialize.rs` | Serialization/deserialization of continuation state to bytes. |
| `store/` | Storage backend implementations (memory, disk, remote). |
| `tiers.rs` | Tiered storage management (hot/warm/cold promotion/demotion). |
| `resume.rs` | Continuation resume logic—restoring execution state. |
| `gc.rs` | Garbage collection for completed or expired continuations. |
| `integrity.rs` | Cryptographic integrity verification for stored continuations. |
| `migration.rs` | Format versioning and migration for continuation data. |
| `README.md` | Subsystem overview, API documentation, usage examples. |
| `GUIDANCE.md` | This file—contribution and quality standards. |

---

## Core Concepts

### What is a Continuation?
A continuation represents "the rest of the computation"—everything needed to resume execution from a suspend point:

- **Stack frames**: Function call chain with local variables.
- **Registers**: Wasm execution state at suspend.
- **Effect context**: Active effect handlers and their state.
- **Capability context**: Granted capabilities for the computation.
- **Metadata**: Timestamp, version, agent ID, correlation IDs.

### Continuation Lifecycle

```
    ┌─────────────┐
    │   Running   │
    │   Agent     │
    └──────┬──────┘
           │ perform effect
    ┌──────▼──────┐
    │   Capture   │ ← Extract execution state
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Serialize  │ ← Convert to bytes
    └──────┬──────┘
           │
    ┌──────▼──────┐        ┌───────────┐
    │   Store     │◄──────►│  Storage  │
    │  (tiered)   │        │  Backend  │
    └──────┬──────┘        └───────────┘
           │ handler completes
    ┌──────▼──────┐
    │    Load     │ ← Retrieve from storage
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Deserialize │ ← Reconstruct state
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   Resume    │ ← Restore execution
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   Running   │
    │   Agent     │
    └─────────────┘
```

---

## Storage Tiers

### Tier Definitions

| Tier | Storage Backend | Latency Target | Durability | Use Case |
| --- | --- | --- | --- | --- |
| **Hot** | In-memory (HashMap) | < 1ms | Process lifetime | Active workflows, rapid resume |
| **Warm** | Local disk / Redis | < 100ms | Node lifetime / replicated | Short-lived suspensions |
| **Cold** | S3 / Database | < 5s | Persistent | Long-term durability, recovery |

### Tier Management

1. **Initial Placement**: New continuations start in hot tier.
2. **Demotion**: Idle continuations demote after configurable TTL.
3. **Promotion**: Access promotes to hotter tier automatically.
4. **Eviction**: Hot/warm tiers have capacity limits; LRU eviction to colder tiers.

### Configuration

```toml
[continuations.tiers]
# Hot tier configuration
hot_capacity_mb = 512
hot_ttl_seconds = 300

# Warm tier configuration
warm_backend = "redis"  # or "disk"
warm_capacity_mb = 4096
warm_ttl_seconds = 3600
warm_redis_url = "redis://localhost:6379"

# Cold tier configuration
cold_backend = "s3"  # or "postgres"
cold_bucket = "diamond-continuations"
cold_ttl_seconds = 604800  # 7 days
```

---

## Serialization Format

### Requirements

1. **Deterministic**: Same state produces identical bytes (for integrity verification).
2. **Versioned**: Include format version for forward compatibility.
3. **Compact**: Minimize storage footprint; support compression.
4. **Self-Describing**: Include schema information for debugging.
5. **Streamable**: Support incremental serialization for large continuations.

### Format Structure

```
┌─────────────────────────────────────────────────────────┐
│ Header (16 bytes)                                       │
│ ├─ Magic: "DMND" (4 bytes)                              │
│ ├─ Version: u16                                         │
│ ├─ Flags: u16 (compression, encryption)                 │
│ └─ Reserved: 8 bytes                                    │
├─────────────────────────────────────────────────────────┤
│ Metadata (variable)                                     │
│ ├─ Agent ID: UUID                                       │
│ ├─ Continuation ID: UUID                                │
│ ├─ Created: u64 (timestamp)                             │
│ ├─ Parent Continuation: Option<UUID>                    │
│ └─ Correlation IDs: Vec<String>                         │
├─────────────────────────────────────────────────────────┤
│ Capability Context (variable)                           │
│ └─ Serialized capability set and attestations           │
├─────────────────────────────────────────────────────────┤
│ Effect Context (variable)                               │
│ └─ Active handlers, pending operations                  │
├─────────────────────────────────────────────────────────┤
│ Execution State (variable)                              │
│ ├─ Wasm memory snapshot                                 │
│ ├─ Wasm globals                                         │
│ ├─ Stack frames                                         │
│ └─ Instruction pointer                                  │
├─────────────────────────────────────────────────────────┤
│ Integrity (32 bytes)                                    │
│ └─ BLAKE3 hash of preceding content                     │
└─────────────────────────────────────────────────────────┘
```

### Serialization API

```rust
pub struct ContinuationSerializer {
    compression: CompressionLevel,
    encryption: Option<EncryptionKey>,
}

impl ContinuationSerializer {
    /// Serialize a continuation to bytes.
    pub fn serialize(&self, cont: &Continuation) -> Result<Vec<u8>>;
    
    /// Deserialize bytes to a continuation.
    pub fn deserialize(&self, bytes: &[u8]) -> Result<Continuation>;
    
    /// Verify integrity without full deserialization.
    pub fn verify_integrity(&self, bytes: &[u8]) -> Result<bool>;
    
    /// Extract metadata without full deserialization.
    pub fn extract_metadata(&self, bytes: &[u8]) -> Result<ContinuationMetadata>;
}
```

---

## Public API

### Core Types

```rust
/// Unique identifier for a continuation.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct ContinuationId(Uuid);

/// Storage tier for continuation placement.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StorageTier {
    Hot,
    Warm,
    Cold,
}

/// Continuation state.
pub struct Continuation {
    pub id: ContinuationId,
    pub agent_id: AgentId,
    pub created_at: Instant,
    pub metadata: ContinuationMetadata,
    pub capability_context: CapabilityContext,
    pub effect_context: EffectContext,
    pub execution_state: ExecutionState,
}

/// Result of a capture operation.
pub struct CaptureResult {
    pub continuation: Continuation,
    pub suspend_point: SuspendPoint,
}

/// Information about a suspend point.
pub struct SuspendPoint {
    pub effect_id: EffectId,
    pub operation: String,
    pub source_location: Option<SourceSpan>,
}
```

### Store Interface

```rust
/// Trait for continuation storage backends.
#[async_trait]
pub trait ContinuationStore: Send + Sync {
    /// Save a continuation, returning its identifier.
    async fn save(&self, cont: &Continuation) -> Result<ContinuationId>;
    
    /// Load a continuation by identifier.
    async fn load(&self, id: ContinuationId) -> Result<Continuation>;
    
    /// Check if a continuation exists.
    async fn exists(&self, id: ContinuationId) -> Result<bool>;
    
    /// Delete a continuation.
    async fn delete(&self, id: ContinuationId) -> Result<()>;
    
    /// List continuations matching a filter.
    async fn list(&self, filter: ContinuationFilter) -> Result<Vec<ContinuationId>>;
    
    /// Get the current storage tier for a continuation.
    async fn tier(&self, id: ContinuationId) -> Result<StorageTier>;
}

/// Tiered store that manages promotion/demotion across tiers.
pub struct TieredContinuationStore {
    hot: Box<dyn ContinuationStore>,
    warm: Box<dyn ContinuationStore>,
    cold: Box<dyn ContinuationStore>,
    config: TierConfig,
}
```

### Capture and Resume

```rust
/// Capture the current execution state as a continuation.
pub fn capture(
    instance: &WasmInstance,
    effect_context: &EffectContext,
    capability_context: &CapabilityContext,
) -> Result<CaptureResult>;

/// Resume execution from a continuation.
pub fn resume(
    store: &mut WasmStore,
    continuation: Continuation,
    resume_value: Value,
) -> Result<ResumeResult>;

/// Result of resuming a continuation.
pub enum ResumeResult {
    /// Execution completed with a final value.
    Completed(Value),
    /// Execution suspended again with a new continuation.
    Suspended(CaptureResult),
    /// Execution failed with an error.
    Failed(RuntimeError),
}
```

---

## Integrity and Security

### Cryptographic Integrity

All stored continuations must be integrity-protected:

1. **Hash Computation**: BLAKE3 hash over serialized content (excluding hash field).
2. **Verification on Load**: Verify hash before deserialization.
3. **Tamper Detection**: Reject continuations with invalid hashes.
4. **Audit Logging**: Log all integrity verification outcomes.

### Optional Encryption

For sensitive continuations:

1. **Encryption at Rest**: AES-256-GCM encryption of serialized state.
2. **Key Management**: Integration with external key management systems.
3. **Key Rotation**: Support re-encryption during tier transitions.

### Capability Preservation

Continuations must preserve and validate capabilities:

1. **Capability Snapshot**: Serialize granted capabilities with continuation.
2. **Validation on Resume**: Verify capabilities are still valid/granted.
3. **Attenuation Check**: Ensure resumed capabilities don't exceed original grant.

---

## Testing Strategy

### Unit Tests

- Capture and resume round-trip correctness.
- Serialization determinism verification.
- Integrity hash computation and verification.
- Tier promotion/demotion logic.

### Integration Tests

- Multi-tier storage workflows.
- Concurrent continuation access.
- Backend-specific behavior (Redis, S3, Postgres).

### Property Tests

- Arbitrary continuation data serialization round-trips.
- Hash collision resistance.
- Concurrent access safety.

### Stress Tests

- High-volume capture/resume throughput.
- Large continuation serialization.
- Tier capacity limits and eviction.

### Fuzz Tests

- Malformed serialized data handling.
- Corrupted header/metadata rejection.
- Invalid integrity hash detection.

---

## Performance Considerations

### Capture Latency
- Target: < 1ms for typical continuations.
- Optimize Wasm memory snapshotting.
- Use incremental capture where possible.

### Serialization Throughput
- Target: > 100 MB/s for large continuations.
- Use zero-copy techniques where possible.
- Support streaming serialization.

### Storage Operations
- Minimize round-trips to storage backends.
- Use connection pooling for remote stores.
- Batch operations where applicable.

### Memory Management
- Use arena allocation for temporary buffers.
- Limit in-memory continuation cache size.
- Implement back-pressure for high load.

---

## Coding Standards

1. **Async by Default**
   - All storage operations are async.
   - Use `tokio` runtime by default.
   - Support cancellation via `CancellationToken`.

2. **Error Handling**
   - Use `thiserror` for error types.
   - Distinguish transient vs. permanent failures.
   - Include continuation IDs in all error contexts.

3. **Logging and Tracing**
   - Use `tracing` for structured logging.
   - Include span information for storage operations.
   - Log tier transitions and evictions.

4. **Metrics**
   - Expose capture/resume latency histograms.
   - Track tier occupancy and hit rates.
   - Monitor serialization sizes.

---

## Quality Checklist (Pre-Merge)

- [ ] Capture and resume correctly preserve execution state.
- [ ] Serialization is deterministic (same input → same bytes).
- [ ] Integrity verification rejects tampered continuations.
- [ ] Tier transitions preserve data integrity.
- [ ] All storage backends pass integration tests.
- [ ] Performance benchmarks meet latency targets.
- [ ] Error handling is comprehensive with rich context.
- [ ] Telemetry covers all critical operations.
- [ ] Documentation includes examples for each API.
- [ ] Security implications documented for new features.

---

## Future Enhancements

- Copy-on-write continuation snapshots for efficiency.
- Delta serialization for incremental updates.
- Distributed continuation storage with sharding.
- Continuation migration across runtime instances.
- Speculative continuation prefetching.
- Time-travel debugging using continuation history.
- Continuation quota management per agent.

---

The continuations subsystem is Diamond's foundation for durable, resumable computation. Every captured state must be perfectly restored; every stored continuation must be tamper-evident. Build with the precision and reliability that long-lived agent workflows demand.