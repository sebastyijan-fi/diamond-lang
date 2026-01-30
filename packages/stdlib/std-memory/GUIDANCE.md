# std-memory Module Guidance

## Purpose
The `packages/stdlib/std-memory/` module provides memory management, caching, and persistence abstractions for Diamond agents. This module enables efficient state management while maintaining Diamond's security guarantees around capability-controlled access and resumable computations. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, capability discipline, and agentic state management.
- **`diamond2.md`** — Tiered continuation storage, durability guarantees, and zero-trust execution.
- **`diamond3.md`** — Algebraic effects, resumable handlers, and module-level capability injection.

Memory management in Diamond is continuation-aware—state must survive suspension and resumption across effect boundaries.

---

## Module Scope

### Core Responsibilities
- **Caching**: In-memory caches with configurable eviction policies.
- **State Containers**: Continuation-safe mutable state wrappers.
- **Serialization**: Utilities for serializing/deserializing agent state.
- **Memory Pools**: Efficient allocation patterns for agent workflows.
- **Persistence Abstractions**: Interfaces for durable state storage.

### Non-Goals
- Low-level memory allocation (handled by runtime).
- Continuation storage implementation (see `packages/runtime/continuations/`).
- Database-specific implementations (use dedicated modules).

---

## Directory Structure

```
std-memory/
├── README.md               # Module documentation and API reference
├── GUIDANCE.md             # This file
├── capabilities.toml       # Capability requirements declaration
├── src/
│   ├── lib.dm              # Module root, public exports
│   ├── cache.dm            # In-memory cache implementations
│   ├── state.dm            # Continuation-safe state containers
│   ├── serialize.dm        # Serialization utilities
│   ├── pool.dm             # Memory pool abstractions
│   └── effects.dm          # Memory-related effect declarations
├── tests/
│   ├── unit/
│   │   ├── cache_test.dm
│   │   ├── state_test.dm
│   │   └── serialize_test.dm
│   ├── property/
│   │   └── cache_properties.dm
│   └── integration/
│       └── continuation_state_test.dm
├── examples/
│   ├── simple_cache.dm
│   ├── agent_state.dm
│   └── persistent_context.dm
└── benches/
    ├── cache_bench.dm
    └── serialize_bench.dm
```

---

## API Design

### Cache API

```diamond
/// A key-value cache with configurable capacity and eviction.
///
/// @capability None (pure in-memory, no external effects)
/// @stability experimental
type Cache[K, V] = {
    capacity: PositiveInt,
    eviction: EvictionPolicy,
    entries: Map[K, CacheEntry[V]],
}

/// Create a new cache with LRU eviction.
///
/// # Example
/// ```diamond
/// let cache = Cache.new[String, User](capacity: 1000)
/// ```
fn new[K, V](capacity: PositiveInt) -> Cache[K, V]

/// Get a value from the cache.
fn get[K, V](cache: Cache[K, V], key: K) -> Option[V]

/// Put a value in the cache, returning evicted entry if any.
fn put[K, V](cache: Cache[K, V], key: K, value: V) -> (Cache[K, V], Option[V])

/// Remove a value from the cache.
fn remove[K, V](cache: Cache[K, V], key: K) -> (Cache[K, V], Option[V])

/// Check if a key exists without updating access time.
fn contains[K, V](cache: Cache[K, V], key: K) -> Bool

/// Eviction policies
enum EvictionPolicy {
    LRU,          // Least Recently Used
    LFU,          // Least Frequently Used
    FIFO,         // First In, First Out
    TTL(Duration) // Time-To-Live expiration
}
```

### Continuation-Safe State

```diamond
/// A state container that survives continuation suspension.
///
/// State values are automatically serialized when continuations
/// are captured and restored on resume.
///
/// @capability None (serialization handled by runtime)
/// @stability experimental
type State[T] where T: Serialize = {
    value: T,
    version: Int,
}

/// Create a new state container.
fn State.new[T](initial: T) -> State[T] where T: Serialize

/// Read the current state value.
fn read[T](state: State[T]) -> T

/// Update the state, returning the new state container.
fn update[T](state: State[T], f: fn(T) -> T) -> State[T]

/// Atomically compare-and-swap state.
fn compare_and_swap[T](
    state: State[T], 
    expected: T, 
    new_value: T
) -> Result[State[T], T] where T: Eq
```

### Serialization Utilities

```diamond
/// Trait for types that can be serialized.
trait Serialize {
    fn serialize(self) -> Bytes
    fn deserialize(bytes: Bytes) -> Result[Self, SerializeError]
}

/// Serialize a value to bytes.
fn to_bytes[T](value: T) -> Bytes where T: Serialize

/// Deserialize bytes to a value.
fn from_bytes[T](bytes: Bytes) -> Result[T, SerializeError] where T: Serialize

/// Serialization formats
enum Format {
    Binary,   // Compact binary format
    Json,     // Human-readable JSON
    Msgpack,  // MessagePack format
}

/// Serialize with specific format.
fn serialize_with[T](value: T, format: Format) -> Bytes where T: Serialize
```

### Memory Pools

```diamond
/// A pool of pre-allocated objects for efficient reuse.
///
/// Useful for agent workflows that frequently create/destroy
/// similar objects (messages, requests, etc.).
///
/// @stability unstable
type Pool[T] = {
    available: Vec[T],
    factory: fn() -> T,
    max_size: PositiveInt,
}

/// Create a new pool with a factory function.
fn Pool.new[T](factory: fn() -> T, max_size: PositiveInt) -> Pool[T]

/// Acquire an object from the pool.
fn acquire[T](pool: Pool[T]) -> (Pool[T], T)

/// Return an object to the pool.
fn release[T](pool: Pool[T], item: T) -> Pool[T]

/// Clear all pooled objects.
fn clear[T](pool: Pool[T]) -> Pool[T]
```

---

## Capability Requirements

The std-memory module is designed to be capability-minimal:

```toml
# capabilities.toml
[module]
name = "std-memory"
version = "0.1.0"
stability = "experimental"

# Core caching and state management require no capabilities
# (pure in-memory operations)

[[optional_capabilities]]
capability = "Persistence"
permissions = ["read", "write"]
justification = "Optional durable state storage for persistent caches"
features = ["persistent-cache"]

[[optional_capabilities]]
capability = "Time"
permissions = ["read"]
justification = "TTL-based cache eviction requires time access"
features = ["ttl-eviction"]
```

---

## Continuation Safety

### State Serialization Rules

For state to survive continuation capture/resume:

1. **Serialize Trait Required**: All state types must implement `Serialize`.
2. **Deterministic Serialization**: Same state produces identical bytes.
3. **Version Compatibility**: Include version tags for migration.
4. **Size Limits**: Respect continuation size limits from runtime config.

### Example: Continuation-Safe Agent Context

```diamond
import std/memory requires {}

/// Agent context that survives suspension.
type AgentContext = {
    conversation_history: Vec[Message],
    user_preferences: Map[String, String],
    session_metadata: SessionMeta,
}

impl Serialize for AgentContext {
    fn serialize(self) -> Bytes {
        // Deterministic serialization
        serialize_with(self, Format.Msgpack)
    }
    
    fn deserialize(bytes: Bytes) -> Result[Self, SerializeError] {
        from_bytes[AgentContext](bytes)
    }
}

/// Create continuation-safe state
let context_state = State.new(AgentContext {
    conversation_history: [],
    user_preferences: {},
    session_metadata: SessionMeta.default(),
})

/// State survives effect suspension
fn process_turn(state: State[AgentContext], input: String) 
    -> String performs LLM 
{
    let ctx = read(state)
    let response = perform LLM.complete(build_prompt(ctx, input))
    
    // Update state (will be serialized if continuation captured)
    let new_state = update(state, |ctx| {
        ctx with { 
            conversation_history: ctx.conversation_history.push(
                Message { role: "assistant", content: response }
            )
        }
    })
    
    response
}
```

---

## Testing Requirements

### Unit Tests

- Cache operations (get, put, remove, eviction).
- State container operations (read, update, compare-and-swap).
- Serialization round-trip for all supported types.
- Pool acquire/release lifecycle.

### Property Tests

- Cache never exceeds capacity.
- LRU eviction is correct (least recent evicted first).
- Serialization is deterministic (same input → same output).
- State versioning is monotonically increasing.

### Integration Tests

- State survives simulated continuation capture/resume.
- Cache works correctly in multi-step agent workflows.
- Pool reuse reduces allocation overhead.

### Performance Benchmarks

- Cache lookup latency (O(1) expected for hash-based).
- Serialization throughput (bytes/second).
- Pool allocation vs. fresh allocation comparison.

---

## Coding Standards

1. **Pure by Default**: Prefer pure functions; isolate effects to dedicated modules.
2. **Immutable Data**: Use immutable data structures; return new containers on mutation.
3. **Generic Design**: Use generics to maximize reusability.
4. **Documentation**: Every public function must have doc comments with examples.
5. **Error Handling**: Use `Result` types; never panic on invalid input.

---

## Quality Checklist (Pre-Merge)

- [ ] All public APIs have comprehensive doc comments.
- [ ] Capability requirements are minimal and documented.
- [ ] Serialization is deterministic and tested.
- [ ] Continuation safety is verified with integration tests.
- [ ] Property tests cover invariants (capacity, eviction order).
- [ ] Benchmarks show acceptable performance.
- [ ] Examples are runnable and demonstrate idiomatic usage.
- [ ] README documents all public APIs with examples.
- [ ] No ambient authority assumptions.
- [ ] State types implement `Serialize` correctly.

---

## Common Patterns

### Agent Session State

```diamond
import std/memory

/// Manage agent session with continuation-safe state
fn create_session() -> State[Session] {
    State.new(Session {
        id: generate_session_id(),
        started_at: perform Time.now(),
        context: AgentContext.default(),
    })
}
```

### Response Caching

```diamond
import std/memory

/// Cache LLM responses to reduce API calls
let response_cache = Cache.new[String, String](
    capacity: 1000,
    eviction: EvictionPolicy.LRU,
)

fn cached_complete(prompt: String) -> String performs LLM {
    match get(response_cache, prompt) {
        Some(cached) -> cached,
        None -> {
            let response = perform LLM.complete(prompt)
            put(response_cache, prompt, response)
            response
        }
    }
}
```

### Object Pooling for Messages

```diamond
import std/memory

/// Pool messages to reduce allocation overhead
let message_pool = Pool.new(
    factory: || Message.empty(),
    max_size: 100,
)

fn create_message(role: String, content: String) -> Message {
    let (pool, msg) = acquire(message_pool)
    msg with { role, content }
}
```

---

## Future Enhancements

- Distributed cache coordination for multi-agent scenarios.
- Write-through and write-behind cache strategies.
- Compression for large state serialization.
- Memory pressure monitoring and adaptive eviction.
- Schema evolution support for state migration.
- Weak references for cache entries.

---

The std-memory module provides the building blocks for efficient, durable state management in Diamond agents. Every abstraction must respect continuation semantics, minimize capability requirements, and enable robust agent workflows that survive suspension and resumption.