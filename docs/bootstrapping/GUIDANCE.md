# Bootstrapping Workspace Guidance

## Purpose
The `docs/bootstrapping/` workspace defines how Diamond’s synthetic corpus, verifier models, and continued pretraining pipelines are conceived, evaluated, and governed. Every asset must reinforce the language’s founding trilogy:

- `diamond.md` — emphasizes intent-oriented agents, capability discipline, and probabilistic decisions.
- `diamond2.md` — details feasibility constraints, synthetic bootstrapping strategy, and runtime security expectations.
- `diamond3.md` — formalizes grammar, semantic typing, algebraic effects, and capability injection semantics.

Use this directory to design reproducible data pipelines that teach models to reason in Diamond while preserving safety, compliance, and alignment with the specification.

---

## Directory Contract
| Subpath | Status | Expected Contents |
| --- | --- | --- |
| `README.md` | present | Orientation, scope, glossary, and cross-links. |
| `pipelines/` | planned | Detailed pipeline specs (transpilation, evolution, verification, packaging). |
| `datasets/` | planned | Dataset manifests, provenance metadata, licensing notes, quality gates. |
| `verifiers/` | planned | Specifications for small language models (SLMs), constrained decoding grammars, evaluation harnesses. |
| `experiments/` | planned | Reports on corpus-generation trials, ablations, and fine-tuning runs. |
| `governance/` | planned | Policies for data acceptance, auditing, redaction, and incident response. |
| `archive/` | planned | Superseded documents with lineage and replacement pointers. |

Add subdirectories only after creating a local guidance note and README to keep the workspace discoverable.

---

## Authoring Standards

1. **Front Matter**  
   ```/dev/null/bootstrapping_doc_front_matter.md#L1-8
   Title: <document title>
   Authors: <maintainers>
   Status: {Draft|In Review|Active|Archived}
   Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
   Last Updated: <ISO date>
   Summary: <2-3 sentence overview>
   Dependencies: <RFCs/issues/datasets>
   ```
2. **Clarity & Rigor**  
   - Use precise terminology (e.g., “synthetic corpus pass,” “verifier model,” “continuation snapshot”).  
   - Prefer normative language (“MUST”, “SHOULD”, “MAY”) when setting policy.

3. **Traceability**  
   - Link to relevant RFCs in `docs/design-decisions/rfcs/`.  
  - Reference implementation locations (`packages/tooling/transpiler`, `scripts/ci`, `benchmarks/`).  
  - Tie commitments to milestones in `docs/spec/roadmap.dm`.

4. **Data Ethics & Compliance**  
   - Document provenance, licensing, and redaction strategies.  
   - Note capability implications (e.g., corpus segments requiring network or filesystem access during generation).  
   - Record reviewer sign-off for sensitive datasets.

5. **Reproducibility**  
   - Provide deterministic configuration files, seeds, and environment specifications.  
   - Store scripts in `scripts/` and reference them here rather than embedding code.

---

## Content Lifecycle

1. **Ideation**  
   - Open an issue summarizing the bootstrapping need, target models, expected outputs, and alignment with the trilogy.  
   - Identify affected working groups (ML Enablement, Language, Runtime, Security, Developer Experience).

2. **Drafting**  
   - Produce an outline; include threat model, data hygiene plan, and success metrics (compile rate, semantic correctness).  
   - Solicit input from compiler/runtime owners to ensure generated samples remain spec-compliant.

3. **Review**  
   - Gather feedback through structured reviews; capture notes in `governance/` or `experiments/`.  
   - Verify that security considerations (capability leakage, malicious prompts) are addressed.

4. **Publication**  
   - Merge with a changelog entry referencing relevant milestones.  
   - Update cross-links (benchmarks, scripts, packages).  
   - Share summary in project communications with required actions for downstream teams.

5. **Maintenance**  
   - Schedule periodic audits (at least quarterly) to ensure docs reflect current pipelines.  
   - Mark obsolete content with `> **Status:** Outdated – see <link>` and create follow-up issues.  
   - Archive superseded workflows in `archive/` with replacement metadata.

---

## Required Sections for Pipeline Docs

- **Objective & Scope** — problem statement, success metrics, non-goals.  
- **Inputs & Provenance** — source datasets, licensing, capability requirements.  
- **Processing Stages** — transpilation, LLM evolution, verification, packaging.  
- **Effect & Capability Considerations** — how generated code models `perform`, continuations, and capability injection.  
- **Quality Gates** — compile rate thresholds, semantic checks, fuzzing targets.  
- **Telemetry & Reporting** — metrics captured (compile %, verifier confidence, decision accuracy), storage locations.  
- **Security & Compliance** — threat model, mitigation strategies, incident response plan.  
- **Operational Steps** — reproducible commands, environment setup, scheduling.  
- **Dependencies** — scripts, packages, benchmarks required for execution.  
- **Open Questions / Risks** — unresolved issues, assumptions, mitigation owners.

---

## Review & Approval Matrix
| Change Type | Required Approvals |
| --- | --- |
| New corpus pipeline or major revision | ML Enablement WG + Language WG |
| Verifier model design / SLM deployment | ML Enablement WG + Security WG |
| Capability-sensitive dataset updates | Security WG + Runtime WG |
| Roadmap milestone adjustments | All affected working groups |
| Tooling automation impacting CI | ML Enablement WG + Developer Experience WG |

Escalate disagreements through the RFC process before merging.

---

## Quality Checklist (Pre-Merge)

- [ ] Document references to `diamond.md`, `diamond2.md`, `diamond3.md` are current.  
- [ ] Pipeline steps enforce grammar, effects, and capability rules from the specification.  
- [ ] Data provenance, licensing, and compliance notes are complete.  
- [ ] Verification strategy (constrained decoding, SLM checks) is explicit.  
- [ ] Telemetry schema and storage plan defined or marked TBD with owner/date.  
- [ ] Security considerations cover prompt injection, capability misuse, and sandboxing.  
- [ ] Changelog and roadmap updates included if scope shifts.

---

## Contribution Etiquette

- Use relative links and consistent naming (`kebab-case`).  
- Annotate TODOs with owner and deadline (`TODO(ml-wg, 2025-01-15): finalize verifier calibration`).  
- Keep “Open Questions” near the top for asynchronous review.  
- Avoid embedding large binaries; reference external storage with access notes.  
- Summarize experiment results succinctly; link to detailed notebooks or dashboards.

---

## Planned Enhancements

- Define a shared `pipeline.schema.json` for pipeline metadata validation.  
- Automate nightly corpus jobs with structured artifacts (aligning with `.github/workflows/nightly.yml`, planned).  
- Integrate benchmark feedback loops so failing samples feed back into corpus refinement.  
- Establish model card templates for verifier SLMs, documenting risk evaluations.  
- Build semantic search across bootstrapping docs using the Diamond `<~>` similarity semantics.

---

Maintaining disciplined bootstrapping guidance ensures Diamond’s synthetic corpus, verifier models, and training pipelines remain reproducible, secure, and faithful to the language’s crystalline intent.