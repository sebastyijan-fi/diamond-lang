# RFC Directory Guidance

## Purpose
The `docs/design-decisions/rfcs/` directory houses active Request For Comments (RFCs) that propose changes to the Diamond language, runtime, tooling, or machine-learning ecosystem. Each RFC must stay grounded in the project’s foundational trilogy:

- `diamond.md` — agentic philosophy, decision semantics, and capability discipline.
- `diamond2.md` — architectural feasibility, synthetic bootstrapping strategy, and security posture.
- `diamond3.md` — grammar, effect semantics, and module-level capability injection rules.

RFCs are the canonical venue for community review before any normative change is accepted.

---

## When to File an RFC
Create an RFC when a proposal will:

- Alter language syntax, typing, or semantics.
- Modify effect handling, continuation mechanics, or runtime execution models.
- Adjust capability policies, security controls, or sandbox assumptions.
- Introduce or revise synthetic corpus pipelines, verifier models, or telemetry contracts.
- Impact developer workflows, major tooling behaviors, or roadmap timelines.

Small fixes or clarifications that do not change normative behavior can proceed directly with issues and PRs, referencing existing decisions.

---

## File Naming & Status
- Use `YYYYMM-<slug>.md` (e.g., `202503-structured-effects.md`).
- Include a `Status` front-matter field with one of: `Draft`, `Review`, `Accepted`, `Rejected`, `Superseded`.
- Move concluded RFCs to `docs/design-decisions/records/` once accepted or rejected, leaving a short stub that links to the record.

---

## Required Front Matter
```/dev/null/rfc_front_matter.md#L1-8
Title: <short descriptive title>
Authors: <owners + contributors>
Status: {Draft|Review|Accepted|Rejected|Superseded}
Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
Working Groups: <Language|Runtime|Security|ML Enablement|Developer Experience>
Related RFCs: <links or “None”>
Last Updated: <ISO date>
Summary: <2-3 sentence overview>
```

---

## Recommended RFC Structure
1. **Context & Motivation** — problem statement, goals, non-goals.
2. **Alignment With Trilogy** — reference relevant clauses and explain compatibility.
3. **Proposal** — detailed design, semantics, algorithms, or policy definitions.
4. **Effects & Capabilities** — impact on `perform`, handlers, continuation storage, and capability manifests.
5. **Security Considerations** — threat analysis, mitigations, sandbox implications.
6. **Operational Impact** — tooling changes, telemetry, documentation, migration guidance.
7. **Alternatives Considered** — explored options and rationale for rejection.
8. **Open Questions** — unresolved issues requiring feedback or follow-up.
9. **Implementation Plan** — milestones, deliverables, dependencies, owners.
10. **Appendices** — supporting benchmarks, prototypes, diagrams.

---

## Review Workflow
1. **Drafting**
   - Open an issue announcing intent.
   - Publish the RFC in this directory and mark `Status: Draft`.
   - Notify relevant working groups.
2. **Discussion**
   - Collect feedback via comments, review meetings, or async channels.
   - Update `Status: Review` once ready for formal consideration.
   - Maintain a changelog section in the RFC summarizing revisions.
3. **Resolution**
   - Secure approvals listed in the Review Matrix (below).
   - Update status to `Accepted` or `Rejected`.
   - Produce a decision record in `docs/design-decisions/records/`.
   - Link implementing issues/PRs and update `CHANGELOG.md` if applicable.
4. **Follow-Through**
   - Track action items until completion.
   - Move superseded drafts to `records/` or `archive/` with annotations.

---

## Review Matrix (Minimum Approvals)
| Proposal Scope                               | Required Working Groups |
|----------------------------------------------|-------------------------|
| Grammar, types, or effect semantics           | Language + Runtime      |
| Runtime capability or security posture        | Runtime + Security      |
| Synthetic corpus, verifiers, or ML pipelines  | ML Enablement + Security|
| Developer tooling and workflow changes        | Developer Experience + Language |
| Roadmap or milestone adjustments              | All affected groups     |

Escalate disagreements through the governance process documented in `docs/design-decisions/README.md`.

---

## Quality Checklist Before Review
- [ ] References to `diamond.md`, `diamond2.md`, `diamond3.md` are accurate.
- [ ] Proposal covers capability and effect implications.
- [ ] Security considerations and mitigations are documented.
- [ ] Telemetry/benchmark impact is described or marked TBD with owner and due date.
- [ ] Implementation plan lists owners, milestones, and dependencies.
- [ ] Alternatives and open questions are clearly enumerated.
- [ ] Links to prototypes, experiments, or benchmarks included where relevant.

---

## Contribution Etiquette
- Keep RFCs focused; open separate documents for unrelated concerns.
- Surface open questions early to invite targeted feedback.
- Use text-based diagrams (Mermaid/PlantUML) stored alongside the RFC when visuals help reasoning.
- Annotate TODOs with responsible parties and deadlines.
- Update status promptly as the RFC progresses through stages.

---

## Future Enhancements
- Automated linting for front matter, status, and link validation.
- Index file enumerating RFCs, owners, and review deadlines.
- Template for AI-assisted RFC drafting aligned with the Diamond specification.
- Integration with release notes and roadmap dashboards to surface accepted decisions.

Maintaining a disciplined RFC process keeps Diamond’s evolution transparent, auditable, and faithful to its crystalline intent.