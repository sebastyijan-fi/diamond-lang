# Diamond (<>) Runtime Specification

**Status:** Draft v0.1  
**Audience:** Runtime engineers, compiler back-end implementers, DevOps operators, security reviewers, and ecosystem tooling authors.

---

## 1. Purpose

The Diamond runtime executes compiled `.dm` modules as WebAssembly (Wasm) components with deterministic, capability-safe semantics. It orchestrates algebraic effects, continuation persistence, capability enforcement, LLM integrations, and inter-component communication.

---

## 2. Architectural Overview

### 2.1 Core Responsibilities
- Load and instantiate Wasm components produced by the Diamond compiler.
- Manage capability handles and enforce object-capability (OCap) policies.
- Dispatch algebraic effects to registered handlers (tooling, prompt router, supervisor, etc.).
- Persist and resume continuations for durable execution.
- Provide observability surfaces (metrics, tracing, logs) for effect lifecycles and capability usage.
- Bridge to host resources (network, filesystem, databases) through audited adapters.

### 2.2 High-Level Components
| Component                 | Description                                                         |
|--------------------------|---------------------------------------------------------------------|
| Loader                   | Validates Wasm modules, capability manifests, and signatures.       |
| Sandbox Engine           | Executes Wasm components with isolation (Linear Memory + WASI).     |
| Capability Manager       | Issues, attenuates, revokes, and audits capability handles.         |
| Effect Dispatcher        | Routes `perform` invocations to registered handlers.                |
| Continuation Store       | Serializes continuations to in-memory cache and durable storage.   |
| Prompt Router            | Executes LLM calls with constrained decoding and verifier checks.   |
| Decision Engine          | Provides embedding similarity and constrained decision runtime.     |
| Supervisor Hub           | Handles escalations, retries, human-in-the-loop workflows.          |
| Telemetry Pipeline       | Exposes logs, traces, metrics, and audit events.                    |

---

## 3. Module Loading & Initialization

1. **Artifact Intake**
   - Accept Wasm component (`*.wasm`) plus manifest (`module.toml`) outlining exported capabilities, required capabilities, effect metadata, and checksum.
   - Validate signatures (Gem registry key or configured authority).
   - Verify manifest matches compiler-produced metadata.

2. **Capability Wiring**
   - Ensure host environment can satisfy required capabilities (per deployment manifest).
   - Inject capability handles into component import table prior to instantiation.
   - Reject module if any capability is unavailable or policy violation detected.

3. **Instantiation**
   - Instantiate Wasm component within sandbox engine.
   - Initialize linear memory, global variables, and optional start function.
   - Register exported entry points (e.g., `main`, `task::execute`) for invocation.

---

## 4. Execution Lifecycle

### 4.1 Invocation Model
- Runtime invokes exported functions with structured arguments (WIT-compatible).
- Each invocation runs inside a *fiber* (lightweight task) with associated capability scope and effect stack.
- Fibers can suspend via algebraic effects; the runtime ensures fairness and cooperative scheduling.

### 4.2 Effect Dispatch Flow
1. Wasm code executes `perform` (lowered to host call).
2. Runtime builds effect record:
   - Effect namespace & operation
   - Serialized arguments
   - Capability context hash
   - Continuation snapshot pointer
3. Dispatcher locates nearest handler (lexical/dynamic) from fiber’s handler stack.
4. Handler executes (in Wasm or host) with arguments + continuation token.
5. Handler either:
   - Calls `resume(result)` to continue computation,
   - Escalates (e.g., `perform Supervisor`),
   - Suspends by persisting continuation without resumption,
   - Throws fatal fault (triggers supervisor or termination).

---

## 5. Continuation Management

### 5.1 Representation
- Continuations captured as opaque blobs containing:
  - Serialized stack frames (registers, locals)
  - Linear memory snapshot diff or pointer to checkpoint
  - Capability manifest hash
  - Effect metadata (effect name, operation, args hash)
  - Integrity signature (runtime private key)

### 5.2 Persistence
- Multi-tier storage:
  - **Hot Cache**: In-memory LRU for quick resume within seconds/minutes.
  - **Warm Store**: Local durable medium (e.g., RocksDB) for medium-term persistence.
  - **Cold Store**: External storage (S3, blob) for long-lived workflows.
- Continuation IDs incorporate timestamp + nonce to avoid collisions.

### 5.3 Resumption Protocol
1. Trigger event (user reply, timer, external message) arrives with continuation ID.
2. Runtime authenticates request (signature validation) and fetches continuation blob.
3. Validate capability manifest availability; abort if missing or revoked.
4. Rehydrate fiber (allocate memory, restore stack/locals, reestablish handler stack).
5. Resume execution by invoking `resume(value)` with trigger payload.

---

## 6. Capability Enforcement

### 6.1 Handle Structure
- Each capability handle contains:
  - Capability name
  - Authority descriptor (hosts, paths, verbs, rate limits)
  - Issuer signature
  - Expiration timestamp
  - Revocation pointer (optional)

### 6.2 Validation
- All host calls (network, filesystem, prompt, etc.) check handle validity:
  - Ensure authority descriptor permits requested action.
  - Check rate limits / quotas, update counters atomically.
  - Verify handle not revoked or expired.
- Attempts to use absent/invalid capability raise `CapabilityError` (effect or fatal).

### 6.3 Attenuation & Delegation
- Runtime exposes host functions for capability attenuation (`restrict`, `split`).
- Delegated handles inherit parent provenance; audit trail records lineage.
- Prevent capability escalation by verifying that derived descriptor ⊆ base descriptor.

---

## 7. Prompt & Decision Execution

### 7.1 Prompt Router
- Maps `prompt` invocations to configured LLM endpoints or local models.
- Applies constrained decoding:
  - Grammar masks (regex, JSON schema, enum)
  - Semantic verifiers (small models for profanity, policy compliance)
- Handles retries, caching (hash of prompt template + args + version).
- Records token usage, latency, and verification results.

### 7.2 Decision Engine (`<>`)
- Maintains embedding service (local vector DB or external API).
- Precomputes embeddings for static case labels at module load.
- On runtime decision:
  - Embed input (via configured model/dimension).
  - Compute similarity to cases; enforce threshold.
  - Invoke fallback if no branch exceeds threshold (or escalate).
- Optionally integrate LLM-based structured decision making when cases involve complex prompts.

---

## 8. Supervisor Framework

- Central coordinator for escalations, policy enforcement, human-in-the-loop.
- Receives `Supervisor` effects with context:
  - Fiber ID, continuation ID
  - Effect payload, stack trace, capability context
  - Proposed remediation (retry, modify args, terminate)
- Strategies:
  - Automatic retries with exponential backoff.
  - Human approval flow (Slack/Email integration).
  - Safety policies (blocklist detection, data loss prevention).
- Supervisors can mutate continuation payload, update capabilities, or kill fibers.

---

## 9. Observability & Telemetry

### 9.1 Metrics
- Per-effect counters (success/fail), latency histograms.
- Continuation counts (captured, resumed, expired).
- Capability usage (calls per capability, attenuation counts).
- Prompt token usage, verification pass/fail.

### 9.2 Logging
- Structured JSON logs with correlation IDs:
  - `runtime.event`: module load, fiber start/stop.
  - `effect.invoke`, `effect.resume`, `effect.error`.
  - `capability.issue`, `capability.restrict`, `capability.revoke`.
  - `continuation.persist`, `continuation.resume`.
- Sensitive data redaction policies enforced at sink.

### 9.3 Tracing
- OpenTelemetry-compatible spans for:
  - Fiber execution segments.
  - External calls (prompt, tool, network).
  - Continuation persistence/resume.
- Spans include capability hashes (not raw descriptors) for privacy.

---

## 10. Deployment Modes

| Mode              | Description                                                | Use Cases                            |
|-------------------|------------------------------------------------------------|--------------------------------------|
| Embedded Runtime  | Library linked into host application (Rust, Go, etc.).     | Edge workers, serverless functions.  |
| Standalone Daemon | Long-lived process managing multiple agents.               | Cloud deployments, on-prem clusters. |
| Clustered Runtime | Distributed scheduler with sharded continuation stores.    | High availability, large fleets.     |
| Sandbox Runner    | Ephemeral container spawning for untrusted components.     | CI/CD, plugin execution.             |

### 10.1 Configuration
- Declarative config file (`runtime.toml`):
  - Capability manifests per stage.
  - Prompt model endpoints & auth.
  - Decision engine parameters (model, thresholds).
  - Continuation storage backends.
  - Supervisor handlers (scripts, webhooks).
  - Observability sinks (metrics, logs, tracing).

---

## 11. Reliability & Fault Tolerance

- Fiber-level isolation: faults within fiber do not crash runtime.
- Supervisor restart policies for faulty modules (circuit breakers).
- Continuation store replication and snapshotting for disaster recovery.
- Health checks:
  - Wasm sandbox integrity
  - Capability issuance service availability
  - Prompt router latency/availability
  - Decision engine health (embedding service)

---

## 12. Security Considerations

- Enforce Wasm sandbox with no host escapes except via declared imports.
- Capability handles signed using runtime key; keys rotated on schedule.
- Continuation payloads encrypted at rest (KMS integration).
- TLS enforced for all external communication.
- Policy engine to restrict module loading (allowlist, signature verification, version pinning).
- Audit logs tamper-evident (hash chains, external storage).

---

## 13. Testing & Validation

- **Unit Tests**: Effect dispatch, capability enforcement, attenuation logic.
- **Integration Tests**: Full workflows with mocked prompt/tool handlers.
- **Deterministic Mode**: Mock random sources and time for reproducibility.
- **Stress Tests**: High concurrency fiber spawning, continuation churn.
- **Fuzzing**: Capability descriptors, effect payloads, Wasm host API inputs.
- **Conformance Suite**: Validates compliance with language spec and ABI contracts.

---

## 14. Roadmap & Open Questions

1. **Distributed Continuations** — Cross-node resumption with consensus guarantees.
2. **Effect Polymorphism** — Static support for generic effect sets in compiled code.
3. **Dynamic Capability Negotiation** — Runtime handshake for capability upgrades.
4. **Hardware Attestation** — TEEs or TPMs for runtime integrity verification.
5. **Multi-model Prompt Execution** — Automatic model selection based on policies.
6. **Predictive Scheduling** — ML-based prioritization of continuation resumption.

All changes to this specification require an RFC referencing prior decisions in `docs/design-decisions/`.

---