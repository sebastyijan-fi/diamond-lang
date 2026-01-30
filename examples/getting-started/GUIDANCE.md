# Getting-Started Examples Guidance

## Purpose
The `examples/getting-started/` directory introduces newcomers to the Diamond (`.dm`) language and runtime. Every example must embody the foundational principles defined in the trilogy:

- **`diamond.md`** — intent-oriented design, capability discipline, and decision semantics (`<>`).
- **`diamond2.md`** — architectural feasibility, secure WebAssembly runtime, and synthetic bootstrapping realities.
- **`diamond3.md`** — grammar, semantic typing, algebraic effects, and module-level capability injection.

The goal is to provide a frictionless on-ramp that teaches secure-by-default execution, resumable effects, and semantic intent capture.

---

## Directory Contract

| Item | Requirement |
| --- | --- |
| Subdirectory per example | Use `examples/getting-started/<example-name>/` with lowercase kebab-case naming. |
| `README.md` | Each example folder must include a README describing scope, setup, execution, and expected output. |
| Alignment metadata | Cite relevant sections of the trilogy and any governing RFCs at the top of each README. |
| Code layout | Place `.dm` files under `src/` when the example spans multiple modules; single-file examples may live at root. |
| Configuration | Store capability manifests, runtime configs, and sample telemetry settings under `config/`. |
| Fixtures | Place deterministic inputs or mock transcripts in `fixtures/`; document provenance. |
| Tests (optional) | Provide smoke tests or scripts under `tests/` or `scripts/` when feasible to validate examples automatically. |

---

## Required Example Types

1. **Hello World & Basics**
   - Minimal program demonstrating syntax, entry point, logging, and exit semantics.
   - Highlight structural typing and module imports.

2. **Effects & Continuations**
   - Show how to declare effects, invoke `perform`, and handle resumable continuations.
   - Include persistence strategy for hot/warm/cold continuation tiers.

3. **Capability Fundamentals**
   - Demonstrate capability requirements, attenuation, and safe usage patterns.
   - Provide manifest examples and note security implications.

4. **Prompt & Decision Primer (Planned)**
   - Illustrate `prompt` declarations and the `< >` decision operator with constrained decoding.

5. **Telemetry & Diagnostics (Planned)**
   - Showcase structured logging, metrics, and trace emission aligned with runtime observability guidance.

---

## Authoring Standards

- **Narrative**: Keep instructions clear, concise, and beginner-friendly while preserving technical accuracy.
- **Consistency**: Align terminology with the specification; avoid introducing unofficial keywords or syntax.
- **Security**: Treat every example as if it will be executed in production. Use explicit capability manifests, avoid ambient authority, and call out potential misuse cases.
- **Resumability**: Explain continuation persistence strategies where effects are involved, even for basic demos.
- **Telemetry**: Encourage inspection of logs, metrics, and traces. Reference shared dashboards or scripts when available.
- **Cross-Linking**: Link to relevant sections of `docs/spec/`, `docs/architecture/`, and `docs/security/` for deeper dives.

---

## README Template Checklist

Each example README should include:

1. **Front Matter**
   ```/dev/null/getting_started_front_matter.md#L1-5
   Title: <Example Name>
   Authors: <Maintainers>
   Status: {Draft|Review|Stable|Deprecated}
   Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
   Last Updated: <ISO date>
   ```
2. **Overview**
   - What the example teaches.
   - Required prerequisites (toolchains, Wasm runtime, environment variables).
3. **Quick Start**
   - Commands to build (`diamondc build`) and run (`diamond-run` or runtime host equivalent).
   - Expected output snippet.
4. **Concepts Covered**
   - Bullet points tied to spec concepts (effects, capabilities, prompt primitives, etc.).
5. **Telemetry & Debugging**
   - How to inspect logs, metrics, traces, and continuation stores.
6. **Security Notes**
   - Capability requirements, threat considerations, and mitigation guidance.
7. **Cleanup**
   - Instructions to remove generated artifacts and reset continuation stores.
8. **Further Reading**
   - Links to additional examples, docs, or RFCs.

---

## Review Workflow

1. **Proposal**
   - File an issue outlining learning objectives, spec alignment, and target audience.
   - Identify reviewing working groups (Language, Runtime, Security, ML Enablement, Developer Experience).

2. **Draft Implementation**
   - Scaffold directory, write code, and document instructions.
   - Ensure commands run on reference platforms (Linux primary).

3. **Peer Review**
   - Validate correctness, security posture, and documentation clarity.
   - Confirm adherence to specification syntax and capability norms.

4. **Publish**
   - Update `examples/README.md` table of contents.
   - Add changelog entry if the example covers new normative ground.

5. **Maintenance**
   - Re-evaluate after spec or toolchain updates.
   - Mark outdated content with `> **Status:** Outdated – see <replacement>` and create follow-up tasks.
   - Archive deprecated examples with rationale once replacements exist.

---

## Quality Checklist (Pre-Merge)

- [ ] Example builds and runs with the current `diamondc` and runtime host.
- [ ] README includes required front matter and execution instructions.
- [ ] Capability manifests are explicit and referenced in documentation.
- [ ] Telemetry guidance is present and verified.
- [ ] Security considerations and failure modes are documented.
- [ ] Code aligns with the latest grammar, effect, and capability rules.
- [ ] Linked to relevant specs, design decisions, and architecture docs.
- [ ] Tests or verification scripts provided (or justified if omitted).

---

## Planned Enhancements

- Automated CI smoke tests for getting-started examples once the compiler/runtime stabilize.
- Example index file (`examples/index.yaml`) with tags, difficulty, and prerequisites.
- Shared assets (mock data, continuation snapshots) with documented provenance.
- Interactive playground integration when the LSP and runtime REPL mature.
- Semantic search across examples using the Diamond `<~>` similarity operator.

---

Maintaining disciplined guidance ensures newcomers experience Diamond as intended—secure, resumable, and semantically aware—while giving maintainers a clear standard for evolving the getting-started catalog.