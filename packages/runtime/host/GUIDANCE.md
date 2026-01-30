# Host Subsystem Guidance

## Purpose
The `packages/runtime/host/` directory implements the host-side interface layer between Diamond agents and their execution environment. This subsystem is responsible for capability management, sandbox enforcement, host function bindings, and telemetry integration. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, zero-trust WebAssembly execution, and security posture.
- **`diamond3.md`** — Module-level capability injection and effect semantics.

The host subsystem is the security boundary—where Diamond's zero-trust promises are enforced.

---

## Directory Contract

| Path | Scope & Expectations |
| --- | --- |
| `capabilities/` | Capability manager, capability types, attenuation logic, manifest parsing. |
| `sandbox/` | Wasm sandbox configuration, resource limits, isolation enforcement. |
| `bindings/` | Host function implementations, WASI integration, platform abstractions. |
| `telemetry/` | Tracing, metrics, logging infrastructure, OpenTelemetry integration. |
| `config/` | Runtime configuration parsing, environment variable handling. |
| `lib.rs` | Public API exports for host functionality. |
| `README.md` | Architecture overview and integration guide. |
| `GUIDANCE.md` | This file—contribution and quality standards. |

---

## Capability Management

### Core Responsibilities

1. **Capability Validation**: Verify that agents possess required capabilities before operations.
2. **Capability Attenuation**: Reduce capability scope when delegating to sub-agents.
3. **Manifest Parsing**: Load and validate capability manifests from Wasm components.
4. **Audit Logging**: Record all capability exercises for security review.

### Capability Types

```rust
/// Core capability representing a specific authority.
pub struct Capability {
    pub id: CapabilityId,
    pub resource: ResourceType,
    pub permissions: PermissionSet,
    pub constraints: Vec<Constraint>,
    pub provenance: Provenance,
}

/// Permission levels for capability operations.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Permission {
    Read,
    Write,
    Execute,
    Delete,
    Admin,
}

/// Constraints that limit capability scope.
pub enum Constraint {
    /// Restrict to specific paths (glob patterns).
    PathPattern(String),
    /// Restrict to network hosts/ports.
    NetworkScope(NetworkConstraint),
    /// Time-based expiration.
    Expiry(DateTime<Utc>),
    /// Rate limiting.
    RateLimit { operations: u32, window_seconds: u32 },
    /// Custom predicate (evaluated at runtime).
    Predicate(ConstraintPredicate),
}
```

### Capability Manifest Format

```toml
# capabilities.toml
[manifest]
version = "1.0"
agent_id = "my-agent"
signature = "base64-encoded-signature"

[[capabilities]]
resource = "filesystem"
permissions = ["read", "write"]
constraints = [
    { type = "path_pattern", value = "/data/**" }
]

[[capabilities]]
resource = "network"
permissions = ["read"]
constraints = [
    { type = "hosts", value = ["api.example.com"] },
    { type = "rate_limit", operations = 100, window_seconds = 60 }
]

[[capabilities]]
resource = "llm"
permissions = ["execute"]
constraints = [
    { type = "models", value = ["gpt-4", "claude-3"] }
]
```

### Capability API

```rust
/// Manager for capability validation and enforcement.
pub trait CapabilityManager: Send + Sync {
    /// Check if a capability set authorizes an operation.
    fn check(&self, caps: &CapabilitySet, op: &Operation) -> Result<(), CapabilityError>;
    
    /// Attenuate capabilities for delegation.
    fn attenuate(&self, caps: &CapabilitySet, restrictions: &[Constraint]) -> CapabilitySet;
    
    /// Load capabilities from a manifest.
    fn load_manifest(&self, manifest: &[u8]) -> Result<CapabilitySet, ManifestError>;
    
    /// Verify manifest signature.
    fn verify_signature(&self, manifest: &Manifest, key: &PublicKey) -> Result<(), SignatureError>;
    
    /// Record capability exercise for audit.
    fn audit(&self, caps: &CapabilitySet, op: &Operation, result: OperationResult);
}
```

---

## Sandbox Enforcement

### Isolation Guarantees

1. **Memory Isolation**: Each agent has its own linear memory space.
2. **No Ambient Authority**: All capabilities must be explicitly granted.
3. **Resource Limits**: CPU, memory, and time quotas are enforced.
4. **Deterministic Execution**: Same inputs produce same outputs (for pure code).

### Resource Limits Configuration

```rust
pub struct ResourceLimits {
    /// Maximum memory in bytes.
    pub max_memory_bytes: u64,
    /// Maximum execution time per invocation.
    pub max_execution_time: Duration,
    /// Maximum fuel (instruction count proxy).
    pub max_fuel: u64,
    /// Maximum number of effect operations per invocation.
    pub max_effects: u32,
    /// Maximum continuation size for serialization.
    pub max_continuation_bytes: u64,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            max_memory_bytes: 256 * 1024 * 1024, // 256 MB
            max_execution_time: Duration::from_secs(30),
            max_fuel: 10_000_000,
            max_effects: 1000,
            max_continuation_bytes: 10 * 1024 * 1024, // 10 MB
        }
    }
}
```

### Sandbox API

```rust
/// Sandbox configuration for agent execution.
pub struct SandboxConfig {
    pub limits: ResourceLimits,
    pub capabilities: CapabilitySet,
    pub environment: HashMap<String, String>,
    pub working_directory: Option<PathBuf>,
}

/// Sandbox instance managing agent isolation.
pub trait Sandbox: Send + Sync {
    /// Execute an agent within the sandbox.
    async fn execute(&self, agent: &WasmComponent, input: Value) -> Result<Value, SandboxError>;
    
    /// Resume a suspended continuation within the sandbox.
    async fn resume(&self, cont: Continuation, value: Value) -> Result<Value, SandboxError>;
    
    /// Query current resource usage.
    fn resource_usage(&self) -> ResourceUsage;
    
    /// Terminate execution immediately.
    fn terminate(&self) -> Result<(), SandboxError>;
}
```

---

## Host Function Bindings

### Binding Categories

| Category | Functions | Capabilities |
| --- | --- | --- |
| Console | `print`, `debug`, `error`, `read_line` | `Console` |
| FileSystem | `read_file`, `write_file`, `list_dir`, `delete` | `FileSystem` |
| Network | `http_request`, `tcp_connect`, `dns_lookup` | `Network` |
| Time | `now`, `sleep`, `set_timer` | `Time` |
| Random | `random_bytes`, `random_int`, `uuid` | `Random` |
| Crypto | `hash`, `sign`, `verify`, `encrypt`, `decrypt` | `Crypto` |
| LLM | `complete`, `embed`, `classify` | `LLM` |

### Host Function Implementation

```rust
/// Trait for implementing host functions.
pub trait HostFunction: Send + Sync {
    /// Function name as exposed to Wasm.
    fn name(&self) -> &str;
    
    /// Required capability for this function.
    fn required_capability(&self) -> Option<CapabilityId>;
    
    /// Execute the host function.
    async fn call(&self, 
                  ctx: &HostContext, 
                  args: &[Value]) -> Result<Value, HostError>;
}

/// Context provided to host functions.
pub struct HostContext {
    pub capabilities: CapabilitySet,
    pub limits: ResourceLimits,
    pub telemetry: TelemetryContext,
    pub continuation_id: Option<ContinuationId>,
}
```

### WASI Integration

The host subsystem provides WASI preview 2 compatibility:

```rust
/// WASI configuration for Diamond agents.
pub struct WasiConfig {
    /// Preopened directories with capability mappings.
    pub preopens: Vec<(PathBuf, Capability)>,
    /// Environment variables (filtered by policy).
    pub env: HashMap<String, String>,
    /// Stdin/stdout/stderr configuration.
    pub stdio: StdioConfig,
    /// Network socket preopens.
    pub sockets: Vec<SocketConfig>,
}
```

---

## Telemetry Integration

### Observability Pillars

1. **Tracing**: Distributed traces across agent boundaries.
2. **Metrics**: Quantitative measurements of runtime behavior.
3. **Logging**: Structured event logs with context.

### Telemetry Configuration

```rust
pub struct TelemetryConfig {
    /// OTLP exporter endpoint.
    pub otlp_endpoint: Option<Url>,
    /// Service name for trace attribution.
    pub service_name: String,
    /// Sampling rate (0.0 to 1.0).
    pub sampling_rate: f64,
    /// Additional resource attributes.
    pub resource_attributes: HashMap<String, String>,
    /// Log level filter.
    pub log_level: Level,
}
```

### Trace Context Propagation

```rust
/// Propagate trace context to agent execution.
pub fn inject_trace_context(ctx: &Context, headers: &mut HashMap<String, String>) {
    // Inject W3C Trace Context headers
    // traceparent, tracestate
}

/// Extract trace context from agent effects.
pub fn extract_trace_context(headers: &HashMap<String, String>) -> Option<Context> {
    // Extract and parse W3C Trace Context
}
```

### Standard Spans

| Span Name | Attributes | Description |
| --- | --- | --- |
| `diamond.agent.execute` | `agent.id`, `input.size` | Top-level agent execution |
| `diamond.effect.perform` | `effect.type`, `operation` | Effect performance |
| `diamond.capability.check` | `capability.id`, `operation` | Capability validation |
| `diamond.continuation.save` | `continuation.id`, `size`, `tier` | Continuation persistence |
| `diamond.host.call` | `function.name`, `args.count` | Host function invocation |

### Standard Metrics

| Metric | Type | Description |
| --- | --- | --- |
| `diamond_agent_executions_total` | Counter | Total agent executions |
| `diamond_agent_execution_duration_seconds` | Histogram | Execution duration |
| `diamond_effects_performed_total` | Counter | Effects performed by type |
| `diamond_capability_checks_total` | Counter | Capability checks by result |
| `diamond_continuation_size_bytes` | Histogram | Continuation sizes |
| `diamond_host_calls_total` | Counter | Host function calls |
| `diamond_resource_usage_memory_bytes` | Gauge | Current memory usage |

---

## Coding Standards

1. **Security First**
   - Validate all inputs from Wasm boundary.
   - Never trust agent-provided data.
   - Use constant-time comparisons for security checks.
   - Log security-relevant events at appropriate levels.

2. **Zero-Copy Where Possible**
   - Use borrowed data across Wasm boundary when safe.
   - Avoid unnecessary allocations in hot paths.
   - Profile memory usage in capability checks.

3. **Error Handling**
   - Use typed errors with rich context.
   - Distinguish user errors from internal errors.
   - Never leak sensitive information in error messages.
   - Include operation IDs for correlation.

4. **Testing**
   - Unit tests for all capability logic.
   - Integration tests with mock Wasm agents.
   - Fuzz tests for manifest parsing.
   - Security-focused tests for bypass attempts.

---

## Development Workflow

### Prerequisites
- Rust toolchain (stable, pinned in `rust-toolchain.toml`).
- `wasmtime` or `wasmer` for Wasm execution.
- OpenTelemetry collector (for telemetry testing).

### Common Commands

```bash
# Build host crate
cargo build -p diamond-host

# Run tests
cargo test -p diamond-host

# Run security-focused tests
cargo test -p diamond-host --features security-tests

# Benchmark capability checks
cargo bench -p diamond-host --bench capability_bench

# Generate documentation
cargo doc -p diamond-host --open
```

---

## Quality Checklist (Pre-Merge)

- [ ] All capability checks validate before operations.
- [ ] Resource limits are enforced without bypass.
- [ ] Host functions require appropriate capabilities.
- [ ] Telemetry spans cover security-relevant operations.
- [ ] No sensitive data in logs or error messages.
- [ ] Manifest parsing rejects malformed input.
- [ ] Signature verification is cryptographically sound.
- [ ] Sandbox isolation is verified by tests.
- [ ] Performance benchmarks show acceptable overhead.
- [ ] Documentation covers security considerations.

---

## Security Review Requirements

Changes to the host subsystem require security review:

| Change Type | Review Requirements |
| --- | --- |
| Capability manager logic | Security WG + Runtime WG |
| Sandbox configuration | Security WG approval |
| New host functions | Security WG + capability mapping |
| Manifest parsing | Security WG + fuzz testing |
| Cryptographic operations | Security WG + external audit |

---

## Future Enhancements

- Hardware security module (HSM) integration for capability signing.
- Remote attestation for capability verification.
- Dynamic capability granting/revocation at runtime.
- Capability delegation audit trails with tamper-evidence.
- Multi-tenancy with per-tenant capability policies.
- Capability visualization and analysis tools.

---

The host subsystem is Diamond's security perimeter. Every line of code here directly impacts the safety of all Diamond agents. Build with paranoid attention to security, comprehensive testing, and thorough documentation. When in doubt, deny access.