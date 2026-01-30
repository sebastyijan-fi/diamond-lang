# Diamond Examples

The `examples/` workspace showcases end-to-end Diamond (<>) programs, agent archetypes, and integration patterns. Every example is curated to demonstrate best practices around structural typing, algebraic effects, capability security, and WebAssembly deployment.

## Directory Guide

- `getting-started/`  
  Entry-level scenarios that help you install toolchains, compile your first `.dm` module, and interact with the runtime.
  - **hello-world.dm** — Minimal program covering syntax, logging, and exit semantics.
  - **effects-intro.dm** — Demonstrates `perform`, `handle`, and resumable continuations in a controlled environment.
  - **capabilities-basics.dm** — Shows how to request, attenuate, and pass capabilities inside a single module.

- `agents/`  
  Opinionated agent blueprints that highlight cognitive patterns and supervisor flows.
  - **react-researcher.dm** — Implements Chain-of-Thought + Action with the Diamond decision operator `< >`.
  - **triage-assistant.dm** — Uses semantic refinements and prompt primitives for incident triage with human escalation.
  - **swarm-coordinator.dm** — Illustrates orchestrating multiple sub-agents via algebraic effects and continuation persistence.

- `integration/`  
  Examples focused on interoperability, deployment, and bridging to existing ecosystems.
  - **python-bridge.dm** — Invokes a sandboxed Python component through the Wasm Component Model.
  - **vector-search.dm** — Combines `std/memory` with external vector stores to run semantic retrieval pipelines.
  - **observability-tour.dm** — Emits structured telemetry, demonstrating logs, metrics, and traces.

## How to Run Examples

1. **Install Tooling**
   - Ensure the Diamond compiler (`diamondc`), runtime host, and language server are built from `packages/`.
   - Install Wasm tools (`wasmtime`/`wasmer`) and required host dependencies as described in `packages/runtime/README.md`.

2. **Compile**
   ```bash
   diamondc build examples/<category>/<example>.dm --out target/<example>.wasm
   ```

3. **Execute**
   ```bash
   diamond-run target/<example>.wasm \
     --capabilities config/capabilities.toml \
     --continuations store/ \
     --log-level info
   ```

4. **Inspect Telemetry**
   - Review logs under `logs/`.
   - Query traces via the configured OpenTelemetry collector.
   - Visualize metrics with the provided dashboards in `benchmarks/`.

## Contribution Workflow

- Keep examples idiomatic and aligned with the current specification (`docs/spec/`).
- Include a README within each subdirectory describing prerequisites, setup steps, and expected output.
- Add automated checks or tests where feasible (e.g., deterministic runs using mocked handlers).
- Reference relevant design decisions (`docs/design-decisions/`) and security guidance (`docs/security/`).
- Submit examples alongside documentation updates and, when necessary, RFC links.

## Roadmap

| Milestone | Description | Status |
|-----------|-------------|--------|
| EX-001 | Populate `getting-started/` with onboarding tutorials | In Progress |
| EX-002 | Publish advanced agent orchestrations with supervisor flows | Planned |
| EX-003 | Add integration showcases for Gem registry packages | Planned |
| EX-004 | Provide reproducible CI harness for example validation | Planned |

---

**Goal:** Make the `examples/` workspace a crystal-clear reference for building diamond-hard agent systems, from “hello world” to production-ready orchestrators.