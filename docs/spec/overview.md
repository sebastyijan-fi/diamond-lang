# Diamond (<>) Language Specification — Overview

This document introduces the core concepts, guiding principles, and high-level semantics of the Diamond programming language. It acts as the map for the detailed specifications that follow in the `docs/spec/` tree.

---

## 1. Purpose

Diamond is an agent-native language that fuses probabilistic reasoning with deterministic execution. It is designed so large language models (LLMs) and humans can co-author secure, verifiable programs that run as WebAssembly (Wasm) components inside an object-capability (OCap) runtime.

---

## 2. Guiding Principles

1. **Agent Ergonomics**  
   Syntax and semantics are optimized for LLM cognition without sacrificing human clarity or auditability.

2. **Security by Construction**  
   Object capabilities, sandboxed execution, and explicit authority make malicious or accidental data exfiltration structurally difficult.

3. **Deterministic Surfaces**  
   Structural typing, semantic refinements, and constrained decoding collapse hallucinations before they reach runtime.

4. **Durable Execution**  
   Algebraic effects and resumable continuations eliminate the need for external workflow engines.

5. **Interoperability**  
   WebAssembly components and signed capability manifests allow Diamond to orchestrate existing ecosystems gradually.

---

## 3. Source Files

- **Extension**: `.dm` (alias `.dia` reserved for interoperable tooling)
- **Module Layout**: one top-level module per file; standard formatting is enforced by the formatter.
- **Capabilities**: declared at the import boundary (`import std/net requires { Network }`).

---

## 4. Language Pillars

### 4.1 Structural Typing

- Types are structural by default; compatibility is determined by field presence and type compatibility.
- Semantic refinement clauses (`where`) attach grammar-based constraints or verifier models.

### 4.2 Algebraic Effects

- Side effects are initiated via `perform` or sugar keywords (e.g., `prompt`).
- Effect usage is explicit at the call site; effect capabilities are inferred through call chains.
- Continuations are serializable, enabling suspension and later resumption of execution.

### 4.3 Probabilistic Control Flow

- The Diamond operator `< >` provides semantic routing between branches based on embedding similarity or constrained LLM decisions.
- Branch blocks require braces to visually delineate probabilistic boundaries.

### 4.4 Object Capabilities

- All authority (network, filesystem, tools) is represented as capability objects.
- Capabilities are injected at module import; there is no ambient authority.
- Attenuation rules allow fine-grained scoping (e.g., network capability restricted to whitelisted hosts).

---

## 5. Core Syntax Elements

| Construct            | Description                                                                    |
|----------------------|--------------------------------------------------------------------------------|
| `struct`             | Structural type declarations with optional defaults and refinements           |
| `type`               | Alias, union, and semantic refinement definitions                              |
| `func`               | Function definitions with explicit return types                               |
| `effect`             | Effect declarations defining resumable operations                              |
| `prompt`             | Typed prompt declarations compiled into constrained LLM calls                  |
| `match` / `case`     | Deterministic pattern matching                                                 |
| `< >`                | Probabilistic decision operator (requires braces for branch bodies)           |
| `perform`            | Initiates an effect (can be sugared by higher-level primitives)               |
| `as`                 | Semantic cast, effectful when invoking LLM-powered transformations             |
| `fallback`           | Explicit default branch for decision blocks                                   |
| `import ... requires`| Module import with capability manifest                                         |

---

## 6. Type System Overview

1. **Structural Records**  
   Comparable by field shape; optional fields allowed.

2. **Enums & Unions**  
   Tagged unions express variant data; pattern matching is exhaustive.

3. **Semantic Refinements**  
   Declared via `where` clauses; compiled to constrained decoding masks or verifier checks.

4. **Generics**  
   Use square brackets (`List[String]`) to avoid ambiguity with `< >`.

5. **Effects in Types**  
   Functions implicitly carry the union of effects they can perform; annotations are inferred and surfaced in tooling.

---

## 7. Effect Semantics

- An effect can suspend computation by capturing a continuation.
- Continuations are serialized as opaque, signed payloads and stored in the runtime’s continuation store.
- Handlers decide whether to resume, fail, or transform the continuation’s arguments.
- Standard effect suite includes `AskUser`, `Tool`, `Supervisor`, `Persist`, `Wait`, with room for user-defined effects.

---

## 8. Runtime & Wasm Integration

1. **Compilation Target**  
   Diamond source is compiled to WebAssembly Component Model modules with explicit capability imports.

2. **Sandboxing**  
   Wasm ensures denial-by-default isolation; capabilities map to host-provided interfaces.

3. **Decision Engine**  
   The runtime maintains embedding caches and resolver logic for `< >` decisions, configurable per deployment.

4. **LLM Execution**  
   Prompt definitions produce deterministic, schema-constrained LLM calls. Verifier models run locally where possible to reduce latency.

---

## 9. Standard Library Surface

- `std/agent`: cognitive patterns (Chain, ReAct, Tree, Graph).
- `std/memory`: vector stores, recall helpers, persistence APIs.
- `std/unit`: dimensional analysis for physical computation.
- `std/net`, `std/fs`, `std/log`: capability-scoped system interfaces.
- Additional modules will emerge via the Gem registry with signed metadata.

---

## 10. Specification Roadmap

1. **Grammar & Lexical Rules** — finalize token definitions, indentation/braces, and error recovery strategy.
2. **Type Checker Semantics** — define structural compatibility, variance, refinement evaluation.
3. **Effect System** — formalize effect typing rules and continuation serialization formats.
4. **Capability Model** — document manifests, attenuation, and verification procedures.
5. **Runtime ABI** — specify Wasm component interfaces, host bindings, and supervisor contracts.
6. **Standard Library Specs** — detail APIs and capability requirements for `std/*` modules.
7. **Testing & Compliance** — define conformance suites, golden tests, and certification process.

---

## 11. References & Further Reading

- `docs/spec/grammar.md` — lexical and syntactic formalism.
- `docs/spec/types.md` — detailed type system rules.
- `docs/spec/effects.md` — algebraic effect semantics.
- `docs/spec/capabilities.md` — OCap model, manifests, and enforcement.
- `docs/spec/runtime.md` — runtime ABI and continuation management.
- `docs/spec/roadmap.dm` — milestone schedule and status tracker.

---

Diamond’s specification is a living document. All changes must go through the RFC process outlined in `docs/design-decisions/`. This overview establishes the north star for contributors and implementers building the “diamond-hard” substrate for the agentic era.