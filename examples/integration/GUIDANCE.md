# Integration Examples Guidance

## Purpose
The `examples/integration/` directory showcases how Diamond (`.dm`) agents interoperate with external systems, Wasm components, host runtimes, and third-party services. Every example must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, capability discipline, and structured decision-making (`<>`).
- **`diamond2.md`** — Architectural feasibility, WebAssembly Component Model integration, and zero-trust runtime execution.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, and module-level capability injection.

Integration examples demonstrate real-world interoperability patterns while maintaining Diamond's security-first, capability-explicit philosophy.

---

## Directory Contract

| Path | Status | Expectations |
| --- | --- | --- |
| `README.md` | planned | Overview of integration categories, prerequisites, and quick-start links. |
| `wasm-components/` | planned | Examples of Diamond agents as Wasm components; host bindings, component composition. |
| `external-apis/` | planned | Interop with REST APIs, databases, message queues (all via explicit capabilities). |
| `host-embedding/` | planned | Embedding Diamond runtime in Rust, Python, or Node.js host applications. |
| `telemetry/` | planned | OpenTelemetry integration, structured logging, distributed tracing setups. |
| `bridges/` | planned | FFI and cross-language bridges (Wasm interface types, capability proxies). |
| `<category>/<example>/` | planned | Each example in its own subdirectory with README, source, config, and tests. |

Before creating a new directory, add a local README describing scope, prerequisites, and reviewers.

---

## Example Structure

Each integration example should follow this layout:

```
<example-name>/
├── README.md           # Purpose, prerequisites, execution steps, expected outputs
├── src/                # Diamond source files (.dm)
├── config/             # Capability manifests, runtime settings, environment templates
├── host/               # Host-side code (Rust, Python, etc.) if embedding Diamond
├── fixtures/           # Mock data, test payloads, expected responses
├── tests/              # Integration test scripts or harnesses
└── docs/               # Additional diagrams, sequence charts, architecture notes
```

---

## Authoring Standards

1. **Metadata**
   - Each example directory must include a `README.md` with:
     - Title, authors, status (`Draft`, `Review`, `Stable`, `Deprecated`).
     - Alignment references (specific sections of the trilogy).
     - External dependencies (host languages, services, APIs).
     - Capability requirements and manifest locations.
     - Execution steps and expected outputs.
     - Troubleshooting and known limitations.

2. **Capability Discipline**
   - All external interactions must go through explicit capability grants.
   - Document capability manifests thoroughly (`capabilities.toml` or `capabilities.json`).
   - Demonstrate capability attenuation when delegating to sub-agents or components.
   - Never embed secrets; use environment variables or mock credentials with provenance notes.

3. **Wasm Component Model Compliance**
   - Follow the Wasm Component Model conventions for imports/exports.
   - Document WIT (Wasm Interface Type) definitions when applicable.
   - Demonstrate component composition patterns (linking, virtualization).
   - Include component dependency graphs in documentation.

4. **Host Integration Patterns**
   - Provide idiomatic host code for each supported embedding scenario.
   - Document runtime initialization, capability injection, and error handling.
   - Show how to handle Diamond effects from the host side.
   - Include teardown and resource cleanup patterns.

5. **Telemetry & Observability**
   - Demonstrate OpenTelemetry integration for traces, metrics, and logs.
   - Show correlation between Diamond agent spans and host spans.
   - Include sample dashboard configurations or queries where helpful.
   - Document performance characteristics and profiling approaches.

6. **Security Considerations**
   - Explicitly document trust boundaries between Diamond and external systems.
   - Show input validation patterns for data crossing boundaries.
   - Demonstrate secure credential handling (environment injection, secret managers).
   - Include threat model summaries for complex integration scenarios.

---

## Integration Categories

### Wasm Component Examples
- Diamond agents packaged as Wasm components.
- Component-to-component linking and composition.
- Virtual filesystem and network capability virtualization.
- Component signing and verification workflows.

### External API Integration
- REST API consumption with typed responses and semantic validation.
- Database access patterns (connection pooling, transaction handling).
- Message queue producers/consumers with durable delivery.
- Event-driven architectures and webhook handling.

### Host Embedding
- Rust embedding with `wasmtime` or similar runtime.
- Python embedding for ML pipeline integration.
- Node.js embedding for web service backends.
- Custom capability providers implemented in host languages.

### Telemetry & Observability
- OpenTelemetry collector configuration.
- Structured logging with semantic context.
- Distributed tracing across agent boundaries.
- Metrics aggregation and alerting patterns.

### Cross-Language Bridges
- Wasm interface types for complex data exchange.
- Capability proxies for legacy system integration.
- Protocol adapters (gRPC, GraphQL, WebSocket).

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the integration scenario.
   - Identify external dependencies and capability requirements.
   - Reference relevant spec sections and architectural patterns.
   - Propose test strategy for the integration.

2. **Implementation**
   - Scaffold directory structure following the template.
   - Implement Diamond code with explicit capabilities.
   - Provide host-side code where applicable.
   - Document all external dependencies and setup steps.

3. **Review**
   - Ensure security review for trust boundary crossings.
   - Validate capability manifests are minimal and justified.
   - Confirm reproducibility across environments.
   - Test teardown and error recovery paths.

4. **Publish**
   - Update `examples/integration/README.md` with entry.
   - Add cross-links to relevant architecture docs.
   - Include in CI smoke tests once toolchain matures.

---

## Quality Checklist

- [ ] README includes metadata, prerequisites, and step-by-step instructions.
- [ ] Capability manifests are explicit, minimal, and documented.
- [ ] External dependencies are version-pinned or range-specified.
- [ ] Host code follows idiomatic patterns for the target language.
- [ ] Security considerations and trust boundaries documented.
- [ ] Telemetry hooks demonstrated or explained.
- [ ] Error handling and recovery patterns shown.
- [ ] Tests cover happy path and failure scenarios.
- [ ] Linked to relevant docs (`docs/architecture/`, `docs/security/`).
- [ ] No secrets or sensitive data committed.

---

## Dependencies & Prerequisites

Integration examples may require:

- Diamond compiler and runtime (once available).
- Wasm runtime (`wasmtime`, `wasmer`, or browser environment).
- Host language toolchains (Rust, Python, Node.js).
- External services (databases, APIs) or their mock equivalents.
- OpenTelemetry collector for observability examples.

Document all prerequisites clearly in each example's README.

---

## Future Enhancements

- CI jobs to validate integration examples against live or mocked services.
- Container-based test environments for reproducible integration testing.
- Example index with tags for integration patterns and complexity levels.
- Reference architectures combining multiple integration patterns.
- Performance benchmarks for cross-boundary calls and capability checks.

---

The `examples/integration/` workspace bridges Diamond's crystalline runtime with the broader software ecosystem. Every example should demonstrate that external interoperability need not compromise security, clarity, or the capability discipline that defines Diamond's philosophy.