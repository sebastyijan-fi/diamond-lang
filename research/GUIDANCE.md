# Research Workspace Guidance

## Purpose
The `research/` workspace documents exploratory investigations, experiments, and technical analyses that advance Diamond’s crystalline vision. Every artifact must remain anchored to the specification trilogy:

- `diamond.md` — intent-oriented language philosophy, decision semantics (`<>`), and capability discipline.
- `diamond2.md` — architectural feasibility, synthetic bootstrapping strategy, runtime security posture.
- `diamond3.md` — grammar, semantic typing, algebraic effects, module-level capability injection.

Use this workspace to capture forward-looking ideas, empirical studies, and formal proofs that inform future RFCs, specifications, and implementation roadmaps.

---

## Directory Contract

| Path | Status | Expected Contents |
| --- | --- | --- |
| `README.md` | planned | High-level orientation, active research themes, contributor index. |
| `programming-models/` | planned | Analyses of language semantics, type systems, effect handlers, continuation models. |
| `runtime-systems/` | planned | Studies on WebAssembly, capability enforcement, sandboxing, performance, observability. |
| `ml-enablement/` | planned | Synthetic corpus generation, verifier models, fine-tuning strategies, evaluation metrics. |
| `security/` | planned | Threat research, attack simulations, capability abuse studies, mitigations. |
| `human-factors/` | planned | Developer experience experiments, prompt ergonomics, UX studies. |
| `bench-notebooks/` | planned | Experimental notebooks (Jupyter, Polaris, etc.) with data provenance. |
| `archive/` | planned | Retired or superseded studies with lineage metadata. |

Create subdirectories only after publishing a local README and guidance snippet documenting scope, owners, and review cadence.

---

## Authoring Standards

1. **Metadata**
   - Each document/notebook requires a front matter block:
     ```
     Title: <concise name>
     Authors: <primary investigators>
     Status: {In Progress|Review|Published|Archived}
     Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
     Working Groups: <Language|Runtime|Security|ML Enablement|Developer Experience>
     Last Updated: <ISO date>
     Summary: <2-3 sentence abstract>
     ```
   - List dependencies, datasets, and external references (papers, repositories).

2. **Reproducibility**
   - Provide scripts or commands to reproduce experiments (link to `scripts/` when applicable).
   - Document environment details (OS, hardware, toolchain versions, model checkpoints).
   - Store deterministic seeds and configuration files; avoid committing large datasets unless explicitly cleared.

3. **Security & Compliance**
   - Redact or separate sensitive information (credentials, proprietary data).
   - Describe capability usage and mitigation strategies for potentially risky experiments.
   - Validate that artifacts respect licensing and attribution requirements.

4. **Traceability**
   - Link related RFCs, issues, benchmarks, and package implementations.
   - Reference roadmap milestones in `docs/spec/roadmap.dm`.
   - Note downstream consumers (e.g., compiler, runtime, ML teams).

5. **Publication Discipline**
   - Summaries of impactful findings belong in `docs/` (spec updates, design decisions) once validated.
   - Archive superseded or invalidated studies with rationale and replacement references.

---

## Research Themes & Examples

- **Language Semantics**: Formalizing effect handlers, continuation serialisation, structural/semantic typing proofs.
- **Runtime & Wasm**: Measuring continuation resume latency, evaluating capability enforcement overhead, sandbox hardening.
- **Synthetic Bootstrapping**: Comparing corpus generation strategies, verifier accuracy, constrained decoding efficiency.
- **Security Analysis**: Prompt-injection resilience, capability misuse simulations, fuzzing results with mitigations.
- **Developer Experience**: Prompt ergonomics, LSP usability studies, human-in-the-loop workflows.

Each study should clarify the hypothesis, experimental design, metrics, and acceptance criteria tied to Diamond’s goals.

---

## Research Workflow

1. **Proposal**
   - File an issue outlining hypothesis, scope, success metrics, required capabilities, and impacted specs.
   - Identify sponsoring working groups and reviewers.

2. **Experimentation**
   - Conduct research in reproducible notebooks or documents.
   - Log intermediate results, anomalies, and decisions.
   - Synchronize code/scripts with the main repository when necessary.

3. **Review**
   - Present findings to relevant working groups.
   - Capture feedback, limitations, and follow-up actions.
   - Decide whether results warrant RFCs, spec changes, or implementation tasks.

4. **Publication**
   - Finalize documentation with summary, detailed results, and supporting artifacts.
   - Update `CHANGELOG.md` or roadmap milestones if outcomes affect commitments.
   - Announce publications in project channels (meeting notes, newsletters, dashboards).

5. **Maintenance**
   - Schedule periodic reviews to ensure conclusions remain valid as the system evolves.
  - Archive outdated research with clear lineage and replacement guidance.

---

## Quality Checklist (Pre-Publication)

- [ ] Hypotheses and objectives clearly stated and aligned with the trilogy.
- [ ] Methodology, datasets, and tooling documented for reproducibility.
- [ ] Results analyzed with supporting data (tables, charts, metrics).
- [ ] Security, capability, and ethical considerations addressed.
- [ ] Recommendations mapped to actionable next steps (RFCs, roadmap, implementation).
- [ ] Cross-links to relevant specs, design decisions, packages, and scripts.
- [ ] Artifacts (code, data, notebooks) organized and referenced; large assets stored externally with access notes.
- [ ] Review sign-off recorded from responsible working groups.

---

## Planned Enhancements

- `research/index.yaml` cataloguing studies, status, owners, datasets, and review dates.
- Automated reproducibility checks (CI jobs executing key notebooks or scripts).
- Template repository for research notebooks with logging, telemetry, and capability guardrails.
- Integration with benchmark dashboards to sync experimental results.
- Semantic search over research artifacts leveraging Diamond’s `<~>` similarity semantics.
- Quarterly synthesis reports summarizing findings and linking to roadmap decisions.

---

Keeping the `research/` workspace disciplined ensures exploratory ideas translate into actionable improvements while safeguarding Diamond’s security, resumability, and semantic precision.