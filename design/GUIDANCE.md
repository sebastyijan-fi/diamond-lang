# Design Workspace Guidance

## Purpose
The `design/` workspace captures forward-looking explorations, user experience studies, and speculative architectures that inform the Diamond language roadmap.
Every artifact must remain consistent with the three foundational specification documents (`diamond.md`, `diamond2.md`, and `diamond3.md`), reinforcing secure-by-default execution, resumable effects, and semantic intent capture.

## Relationship to the Specification Trilogy
- **`diamond.md` — Crystal Protocol**: Anchor high-level language philosophy, agentic intent primitives, and capability commitments.
- **`diamond2.md` — Architectural Feasibility**: Ground runtime feasibility studies, tooling proposals, and migration strategies.
- **`diamond3.md` — Semantic Specification**: Reference grammar, effect semantics, and capability injection rules when drafting detailed designs.

When proposing ideas that stretch or reinterpret the trilogy, include a reconciliation note that explains: rationale, affected sections, and whether an RFC is required.

## Directory Structure Expectations
| Subpath | Status | Contents |
| --- | --- | --- |
| `playbooks/` | planned | Scenario-driven design experiments (agent UX, runtime orchestration, onboarding flows). |
| `ux/` | planned | Research on developer ergonomics, editor flows, and learning journeys. |
| `experiments/` | planned | One-off prototypes, alternative syntaxes, or runtime spikes. |
| `reviews/` | planned | Design review notes, stakeholder feedback, and consensus records. |
| `reference/` | planned | Curated external research, benchmarks from other languages, comparative analyses. |

Create subdirectories only when a corresponding guidance note and README exist to keep the workspace navigable.

## Artifact Types & Required Metadata
Each design document must begin with a front matter block:
```/dev/null/design_doc_front_matter.md#L1-8
Title: <concise name>
Authors: <working group owners + contributors>
Status: {Draft|In Review|Adopted|Archived}
Spec Alignment: <sections of diamond.md/diamond2.md/diamond3.md>
Related RFCs: <links or “None”>
Last Updated: <ISO date>
Summary: <2-3 sentence problem framing>
```

Additional metadata guidelines:
- Link to relevant issues, RFCs, and roadmap milestones.
- Record decision outcomes and follow-up tasks in a closing checklist.
- For concept art or diagrams, store source files alongside exported assets.

## Working Group Collaboration Model
1. **Initiate** — Author drafts proposal outline, ensuring scope maps to one or more roadmap milestones.
2. **Triangulate** — Share outline with the responsible working groups (Language, Runtime, Security, ML Enablement, Developer Experience) for early validation.
3. **Deep Dive** — Conduct research spikes or prototypes; capture findings in `experiments/` with reproducible instructions.
4. **Synthesize** — Update the main design document with lessons learned, explicit trade-offs, and impact on specification text.
5. **Hand Off** — Open or update RFCs under `docs/design-decisions/rfcs/` when implementation changes are required.

Document all synchronous review sessions—notes belong in `reviews/` with timestamps, attendees, and decisions.

## Decision Hygiene
- Highlight contested assumptions and mitigation strategies.
- Record opposing viewpoints; unresolved disagreements require an owner and deadline.
- Maintain a decision log section that links to:
  - Adopted RFCs.
  - Blocked items awaiting data.
  - Experiment outcomes (success, partial, failure).

## Experimentation Guidelines
- Prototype code should live outside the main implementation packages to avoid confusing contributors.
- Provide setup instructions, capability manifests, and teardown steps.
- Tag experiments with an explicit lifespan (e.g., sunset after milestone M2 unless renewed).
- Capture metrics or qualitative feedback that justify design evolutions.

## UX Research Artifacts
- Use mixed methods: developer journaling, usability tests, prompt transcripts, and metric dashboards.
- Anonymize participant data and store consent records separately (never inside repository if sensitive).
- Summaries must map findings to actionable changes in toolchain, language features, or documentation.
- Provide before/after flows demonstrating how proposals reduce cognitive load or improve effect handling clarity.

## Review & Approval Workflow
- **Draft**: Open issue describing intent; attach outline.
- **In Review**: Schedule design review; collect feedback in `reviews/`.
- **Adopted**: Link to merged RFC or implementation issue; update `Status`.
- **Archived**: Move outdated or superseded designs to an `archive/` subfolder with rationale.

Approval quorum defaults:
- Language semantics: Language + Runtime leads.
- Security posture shifts: Security lead + Runtime lead.
- ML data pipelines: ML Enablement lead + Tooling lead.
- Developer experience tooling: Developer Experience lead + Language lead.

## Traceability & Sync Points
- Reference roadmap checkpoints from `docs/spec/roadmap.dm`.
- Cross-link to ongoing tasks in `scripts/`, `packages/`, and `docs/spec/` to ensure implementation follows design intent.
- Update `CHANGELOG.md` when a design materially alters public commitments.
- Include a retrospective section once a design reaches implementation to capture lessons learned.

## Quality Bar Checklist
- [ ] Alignment with `diamond.md`: preserves intent-oriented agents, capability discipline, and probabilistic decisions.
- [ ] Alignment with `diamond2.md`: acknowledges runtime feasibility, bootstrapping constraints, and Wasm component model.
- [ ] Alignment with `diamond3.md`: respects grammar, effect semantics, and module capability injection.
- [ ] Risk analysis: security, resilience, and misuse scenarios considered.
- [ ] Resumability plan: how the design supports continuation storage, handler composition, or effect retries.
- [ ] Telemetry plan: metrics or qualitative signals proving success.
- [ ] Sunset criteria: conditions for deprecating or revising the design.

## Contribution Etiquette
- Use plain language supplemented by precise terminology; avoid marketing fluff.
- Prefer diagrams generated from source (Mermaid, PlantUML) over bitmap assets.
- Keep change logs concise but explicit; note intent, scope, and resulting actions.
- Encourage asynchronous review by summarizing key questions at the top of each document.

## Future Enhancements
- Establish template repository for design playbooks with reusable experiment harnesses.
- Integrate lightweight model reviewers that flag semantic drift from the specification trilogy.
- Automate cross-links between design documents and active RFCs or implementation tasks.
- Create periodic synthesis reports summarizing design evolution and spec touchpoints.

---
Maintaining a disciplined `design/` workspace ensures Diamond’s language, runtime, and ecosystem decisions remain transparent, evidence-driven, and faithful to the project’s crystalline vision.