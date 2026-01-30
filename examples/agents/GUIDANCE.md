# Agents Examples Guidance

## Purpose
The `examples/agents/` directory houses canonical demonstrations of Diamond (`.dm`) agent archetypes. Each example illustrates how structured decision-making, capability discipline, and resumable effects combine to create robust, auditable agentic systems. All content must align with the foundational trilogy:

- **`diamond.md`** — Agentic philosophy, intent capture, Diamond operator semantics (`<>`), capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, zero-trust Wasm execution.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, module-level capability injection.

---

## Directory Contract

| Path | Status | Expectations |
| --- | --- | --- |
| `README.md` | planned | Overview of agent archetypes, quick-start links, difficulty ratings. |
| `react/` | planned | ReAct (Reasoning + Acting) loop demonstrations with tool orchestration. |
| `supervisor/` | planned | Hierarchical supervisor–worker coordination patterns. |
| `swarm/` | planned | Multi-agent swarm orchestration with capability delegation. |
| `conversational/` | planned | Stateful dialog agents with resumable session handling. |
| `tool-use/` | planned | Focused examples of typed tool invocation and result routing. |
| `human-in-the-loop/` | planned | Approval workflows with continuation suspension across human input. |
| `<archetype>/` | planned | Additional archetypes as patterns emerge from community needs. |

Each subdirectory must contain:
- A `README.md` describing purpose, prerequisites, alignment with spec sections, and execution instructions.
- One or more `.dm` source files implementing the pattern.
- A `config/` folder (if needed) for capability manifests and runtime settings.
- Optional `fixtures/` for deterministic test data and mock transcripts.

---

## Archetype Design Principles

1. **Single Teaching Goal**
   - Each example focuses on one architectural pattern or capability usage.
   - Avoid mixing concerns (e.g., a ReAct loop example should not also demonstrate complex swarm coordination).

2. **Explicit Capability Wiring**
   - Demonstrate `import ... requires { ... }` for all external authorities.
   - Ship `capabilities.toml` or equivalent manifests explaining required permissions.
   - Highlight capability attenuation when delegating to sub-agents.

3. **Effect Handler Clarity**
   - Show explicit `perform` calls for I/O, tool invocation, and human approval.
   - Include effect handler blocks that illustrate resumption and error recovery.
   - Document continuation persistence expectations where applicable.

4. **Decision Operator Usage**
   - Use the Diamond operator `<>` to demonstrate structured probabilistic branching.
   - Annotate branches with semantic intent and routing rationale.
   - Show how decision blocks interact with capability constraints.

5. **Security Awareness**
   - Document threat scenarios (prompt injection, capability misuse) in the README.
   - Demonstrate mitigations: input validation, capability scoping, sandboxed execution.
   - Avoid hardcoded secrets; use mock credentials with provenance notes.

6. **Observability**
   - Emit structured logs, traces, and metrics where pedagogically valuable.
   - Reference observability scripts in `scripts/` or dashboards in `benchmarks/`.

---

## Suggested Archetypes

### ReAct Loop (`react/`)
- Reasoning→Action→Observation cycle with tool orchestration.
- Demonstrate semantic type constraints on tool outputs.
- Show early termination and retry logic via effect handlers.

### Supervisor–Worker (`supervisor/`)
- Hierarchical delegation with capability attenuation.
- Supervisor manages task routing; workers execute scoped sub-tasks.
- Illustrate continuation handoffs between agents.

### Swarm Orchestration (`swarm/`)
- Peer-to-peer agent collaboration with shared context.
- Demonstrate consensus or voting mechanisms using decision operators.
- Show capability federation across swarm members.

### Conversational Agent (`conversational/`)
- Multi-turn dialog with session state persistence.
- Demonstrate continuation suspension/resumption across user messages.
- Show context window management and summarization strategies.

### Tool-Use Patterns (`tool-use/`)
- Typed tool declarations and invocation semantics.
- Demonstrate constrained decoding for structured outputs.
- Show error handling and fallback strategies.

### Human-in-the-Loop (`human-in-the-loop/`)
- Approval workflows requiring human confirmation.
- Demonstrate continuation suspension until external input arrives.
- Show audit trails and decision logging.

---

## Authoring Standards

1. **Metadata (README.md front matter)**
   ```
   Title: <example title>
   Authors: <contributors>
   Status: {Draft|Review|Stable|Deprecated}
   Difficulty: {Beginner|Intermediate|Advanced}
   Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
   Prerequisites: <required knowledge, tools, or capabilities>
   Last Updated: <ISO date>
   ```

2. **Source Organization**
   - Place `.dm` files in `src/` when multiple modules exist.
   - Use `main.dm` as the entry point.
   - Keep configuration separate from source code.

3. **Execution Instructions**
   - Provide step-by-step commands to run the example.
   - Document expected outputs and how to verify success.
   - Include troubleshooting tips for common issues.

4. **Testing**
   - Provide deterministic test cases or validation scripts where feasible.
   - Reference fixtures for reproducible runs.
   - Note any non-deterministic behavior (LLM outputs) and how to validate semantically.

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the archetype: teaching goals, target audience, spec alignment.
   - Identify reviewers from Language, Runtime, Security, and Developer Experience WGs.

2. **Implementation**
   - Scaffold the directory structure with README and source files.
   - Follow coding conventions (square-bracket generics, explicit effects, capability imports).
   - Add inline comments referencing spec sections for nuanced behaviors.

3. **Review**
   - Ensure correctness, capability hygiene, and pedagogical clarity.
   - Validate against current compiler/runtime (once available) or document expected behavior.
   - Check security considerations and observability hooks.

4. **Publication**
   - Update `examples/agents/README.md` (or create it) with the new archetype listing.
   - Add changelog entries if the example establishes normative patterns.
   - Link to relevant RFCs or design decisions.

5. **Maintenance**
   - Revisit examples when spec or tooling changes affect behavior.
   - Mark outdated examples with deprecation notices and replacement links.
   - Archive superseded examples to `examples/archive/` (planned) with rationale.

---

## Quality Checklist

- [ ] README includes metadata, alignment references, and execution instructions.
- [ ] Code follows Diamond syntax conventions and compiles with current toolchain (or behavior documented).
- [ ] Capability manifests are explicit, minimal, and justified.
- [ ] Effect handlers demonstrate resumption and error recovery.
- [ ] Decision operator usage is annotated with semantic intent.
- [ ] Security considerations documented with mitigations.
- [ ] Observability hooks present where pedagogically valuable.
- [ ] Tests or validation scripts provided for reproducibility.
- [ ] Linked to relevant docs (`docs/spec/`, `docs/architecture/`, `docs/security/`).

---

## Future Enhancements

- CI smoke tests for agent examples once compiler/runtime are available.
- Interactive playground integration for browser-based execution.
- Difficulty-rated learning paths connecting examples progressively.
- Template generator for new agent archetypes with security and observability scaffolding.
- Semantic search across examples using Diamond's `<~>` similarity semantics.

---

The `agents/` directory is the showcase for Diamond's agentic vision. Every example should demonstrate that autonomous systems can be safe, auditable, and brilliantly expressive. Contribute patterns that make robust agent engineering accessible to the community.