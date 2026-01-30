# Diamond (<>) Capability Security Specification

**Status:** Draft v0.1  
**Audience:** Language designers, compiler/runtime implementers, security reviewers, Gem registry maintainers.

---

## 1. Purpose

This document defines the capability-based security (OCap) model for Diamond. It formalizes how authority is represented, exchanged, attenuated, and audited across the language, compiler, runtime, and ecosystem tooling. The specification ensures that Diamond programs are *secure by construction* and that ambient authority is structurally impossible.

---

## 2. Core Principles

1. **No Ambient Authority** — Code cannot access resources without an explicit capability reference.
2. **Fine-Grained Delegation** — Capabilities can be attenuated (restricted) before being passed to callees.
3. **Deterministic Surfaces** — Capability requirements are evident at module boundaries, enabling static review.
4. **Sandbox Enforcement** — WebAssembly components enforce capability handles at runtime, isolating untrusted code.
5. **Provable Provenance** — Capabilities are cryptographically signed, auditable, and traceable through the Gem registry.

---

## 3. Capability Object Model

### 3.1 Capability Definition

Capabilities are first-class types that encode the authority to perform an action against a protected resource.

```dm
capability Network:
    allow hosts: ["api.stripe.com", "api.twilio.com"]
    deny methods: ["DELETE"]
    rate_limit: 100 per Minute
```

**Key properties:**

- **Identifier** — Unique name (e.g., `Network`, `Filesystem.Read`).
- **Authority Descriptor** — Declarative rules (allowed hosts, paths, verbs, quotas).
- **Metadata** — Expiration, issuer, cryptographic signature, optional annotations.

### 3.2 Storage & Transfer

- Capabilities are opaque handles (references) that cannot be forged.
- Copy semantics are deliberate: default is *move* to prevent uncontrolled duplication; *share* must be explicitly requested via annotations.
- Serialization of capabilities is disallowed unless an encoder capability is present (prevents exfiltration via data channels).

### 3.3 Attenuation

Attenuation produces a derived capability with reduced authority.

```dm
let net = capability Network
let payments_net = net.restrict(hosts = ["api.stripe.com"], methods = ["POST"])
```

- Attenuation is monotonic (authority only shrinks).
- Attenuation rules are validated at compile-time and runtime.

---

## 4. Language Integration

### 4.1 Module Imports

Modules declare required capabilities in their `import` clauses:

```dm
import std/net requires { Network }
import std/fs requires { ReadOnlyFs }
```

- The compiler verifies that any call to capability-protected APIs is within the scope of an imported capability.
- Dependency graphs reveal capability usage, enabling static audits.

### 4.2 Function Signatures

Capabilities are passed explicitly via parameters or closures:

```dm
func charge(card: CardInfo, amount: Money, net: Network) -> Result[Receipt]:
    return perform PaymentGateway.charge(card, amount, net)
```

- Tooling warns if a capability is threaded beyond the minimal necessary scope.
- Capability escape analysis identifies leaks (capability stored in global/static context).

### 4.3 Effects & Capabilities

Effects specify required capabilities through metadata:

```dm
effect ToolCall(name: String, payload: Json) -> ToolResult:
    @requires Capability.Tool
```

- The effect system propagates capability requirements through continuations.
- Handlers must present matching capabilities to resume.

---

## 5. Compiler Responsibilities

1. **Static Verification**
   - Detect unauthorized resource usage.
   - Ensure capability attenuation rules do not widen authority.
   - Enforce that `.restrict` operations produce strictly narrower capabilities.

2. **Dataflow Analysis**
   - Track capability flow through variables, closures, and continuations.
   - Emit diagnostics when capabilities cross module boundaries unintentionally.

3. **ABI Generation**
   - Emit capability import tables in Wasm modules.
   - Encode capability manifests in component metadata for host verification.

---

## 6. Runtime Enforcement

### 6.1 Capability Handles

- Runtime maps capability objects to sandbox handles.
- Wasm host functions validate handles before executing side effects.
- Capabilities contain nonces to prevent replay attacks.

### 6.2 Continuations

- Continuation payloads include capability manifest hashes.
- Resumption fails if the runtime cannot supply the same or stronger capabilities.

### 6.3 Revocation

- Capabilities may be revocable:
  - *Soft revocation*: runtime marks handle as invalid and errors on future use.
  - *Hard revocation*: runtime tears down executing contexts that still hold the handle.
- Revocation lists are distributed via secure channels (Gem registry or deployment configs).

---

## 7. Gem Registry & Supply-Chain Security

1. **Signed Capability Manifests**
   - Packages define required/exported capabilities in `gem.toml`.
   - Signatures bind capability requirements to specific code hashes.

2. **Fuzzy Import Detection**
   - Compiler warns on capability names similar to known ones (`NetworkAccess` vs. `Network`).

3. **Trusted Capability Authorities**
   - Organizations can publish capability profiles (e.g., “payment-processing”) with audited descriptors.
   - Registry enforces issuer policies, preventing unverified capability escalation.

---

## 8. Auditing & Observability

- Runtime emits structured events:
  - `capability_request`, `capability_grant`, `capability_restrict`, `capability_revoke`.
- Audit logs link actions to:
  - Module + version
  - Capability hash
  - Call stack trace (symbolized)
  - Continuation ID (if applicable)

- Observability tooling provides:
  - Capability usage heatmaps
  - Leak detection dashboards
  - Policy compliance reports

---

## 9. Testing & Verification

- **Static Tests**: Capability conformance tests run during CI (e.g., ensuring no network calls exist without `Network` capability).
- **Dynamic Tests**: Mock capabilities for deterministic tests; verify revocation and attenuation logic.
- **Property-Based Tests**: Ensure attenuation never expands authority; fuzz capability creation/destruction.

---

## 10. Deployment Guidance

1. **Capability Manifests**
   - Each deployment environment must supply a manifest mapping capability names to host resources (e.g., network endpoints, directories).

2. **Least Authority Configuration**
   - Default manifests expose minimal sets; developers must opt-in to additional authority.

3. **Isolation Policies**
   - Combine capabilities with Wasm sandboxing and containerization.
   - Deploy capability issuance services (HSM-backed) for sensitive resources.

---

## 11. Open Questions & RFC Hooks

1. **Capability Polymorphism** — Generics over capability types for reusable components.
2. **Distributed Capability Delegation** — Secure cross-runtime capability passing (e.g., between microservices).
3. **Capability Expiration** — Formal semantics for time-bound capabilities and renewal flows.
4. **Capability Proof-Carrying Code** — Embedding formal proofs in capability descriptors.
5. **Attestation & Hardware Roots** — Integration with TEEs or TPMs for issuance and verification.

Updates to this specification require an RFC in `docs/design-decisions/` referencing relevant security reviews and threat models.

---