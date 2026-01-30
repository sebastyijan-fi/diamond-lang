# Design Decisions Workspace Guidance

## Purpose
The `docs/design-decisions/` workspace records the governance history of the Diamond language. Every artifact must stay aligned with the specification trilogy:

- `diamond.md` — articulates the agentic philosophy, decision semantics, and capability discipline.
- `diamond2.md` — validates architectural feasibility, synthetic bootstrapping strategy, and security posture.
- `diamond3.md` — formalizes grammar, effect semantics, and module-level capability injection.

Use this directory to capture the rationale, trade-offs, and consensus around any change that affects the language, runtime, tooling, or ML ecosystem.

---

## Directory Contract

| Subpath           | Status  | Expected Contents |
|-------------------|---------|-------------------|
| `README.md`       | present | Overview of process, quick links, glossary. |
| `rfcs/`           | planned | Request-for-Comment documents under active consideration. |
| `records/`        | planned | Accepted/rejected decisions with final rationale. |
| `templates/`      | planned | Markdown templates for RFCs, decision records, meeting notes. |
| `archive/`        | planned | Superseded governance artifacts with lineage metadata. |

Create subdirectories only when a local README and guidance note exist so contributors understand expectations.

---

## Authoring Standards

1. **Front Matter**  
   ```/dev/null/design_decision_front_matter.md#L1-7
   Title: <document title>
   Authors: <owners + contributors>
   Status: {Draft|Review|Accepted|Rejected|Superseded}
   Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
   Related RFCs: <links or “None”>
   Last Updated: <ISO date>
   Summary: <2-3 sentence overview>
   ```
2. **Traceability**  
   - Link to issues, pull requests, benchmarks, and relevant code paths.  
   - Reference roadmap milestones (`docs/spec/roadmap.dm`) and affected working groups.
3. **Normative Voice**  
   - Use RFC 2119 keywords for requirements.  
   - Clearly separate facts, assumptions, and open questions.
4. **Evidence**  
   - Cite experiments, benchmarks, or security reviews that inform the decision.  
   - Attach appendices for detailed data, keeping the main document concise.

---

## Lifecycle Workflow

1. **Proposal Intake**  
   - Open an issue summarizing the change, scope, and impacted components.  
   - Draft an RFC in `rfcs/` using the template; note alignment with the trilogy.
2. **Review & Discussion**  
   - Assign reviewers from relevant working groups (Language, Runtime, Security, ML Enablement, Developer Experience).  
   - Capture meeting notes or async feedback in the RFC discussion section.
3. **Decision**  
   - Once consensus is reached, create a decision record in `records/` summarizing outcomes, alternatives considered, and required follow-up actions.  
   - Update status badges (e.g., `Accepted`, `Rejected`, `Superseded`).  
   - Link the decision to the associated RFC, issue, and code changes.
4. **Implementation Tracking**  
   - Ensure follow-up tasks are filed and linked (compiler/runtime updates, documentation changes, benchmark adjustments).  
   - Update `CHANGELOG.md` when the decision affects public commitments.
5. **Archival**  
   - Move superseded RFCs or records to `archive/` with a header noting the replacement and effective date.

---

## Review & Approval Matrix

| Decision Type                            | Required Approvals |
|----------------------------------------- |--------------------|
| Language grammar & type system           | Language WG + Runtime WG |
| Effect semantics & continuation model    | Language WG + Runtime WG |
| Capability policies & security posture   | Runtime WG + Security WG |
| Synthetic corpus & verifier pipelines    | ML Enablement WG + Security WG |
| Tooling & developer experience changes   | Developer Experience WG + Language WG |
| Roadmap or milestone adjustments         | All impacted working groups |

Escalate contentious topics via a formal RFC before merging dependent work.

---

## Quality Checklist (Pre-Merge)

- [ ] Alignment with `diamond.md`, `diamond2.md`, and `diamond3.md` explicitly documented.  
- [ ] Alternatives, risks, and mitigations captured.  
- [ ] Impact on capabilities, effects, and resumability addressed.  
- [ ] Telemetry or benchmark implications noted (or marked TBD with owner/deadline).  
- [ ] Follow-up tasks, owners, and due dates enumerated.  
- [ ] Cross-links to implementation PRs, tests, docs, and benchmarks added.  
- [ ] Status and metadata updated (front matter, changelog, roadmap).

---

## Contribution Etiquette

- Keep RFCs tightly scoped; use separate documents for orthogonal proposals.  
- Place open questions near the top to aid asynchronous reviewers.  
- Prefer text-based diagrams (Mermaid/PlantUML) stored alongside the document.  
- Annotate TODOs with owners and deadlines (`TODO(runtime-wg, 2025-02-01)`), removing them once resolved.  
- Avoid duplicating content; reference authoritative specs or architecture docs instead.

---

## Planned Enhancements

- Establish automated linting for front matter, status consistency, and broken links.  
- Add an index (`index.yaml`) enumerating active RFCs, owners, and review deadlines.  
- Integrate decision log summaries into release notes and roadmap checkpoints.  
- Provide guidance for AI-assisted RFC drafting with guardrails tied to the specification trilogy.  
- Build semantic search across decision documents using Diamond’s `<~>` similarity semantics once available.

---

Maintaining a disciplined design-decision workspace ensures Diamond’s evolution remains transparent, auditable, and faithful to its crystalline language vision.