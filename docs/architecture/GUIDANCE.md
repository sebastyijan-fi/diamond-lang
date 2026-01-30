# Architecture Documentation Guidance

## Purpose
The `docs/architecture/` workspace captures system-wide design narratives, deployment blueprints, and operational playbooks for the Diamond stack. Every artifact must align with the specification trilogy:

- `diamond.md` — establishes the intent-oriented philosophy, capability discipline, and decision semantics.
- `diamond2.md` — validates runtime feasibility, synthetic bootstrapping, and zero-trust execution.
- `diamond3.md` — codifies grammar, algebraic effects, and module-level capability injection.

Use this directory to describe how the philosophy crystallizes into concrete runtime topologies, orchestration patterns, and operational safeguards.

## Directory Contract
| Subpath | Status | Expected Contents |
| --- | --- | --- |
| `README.md` | present | High-level orientation, architectural overview, entry points to detailed documents. |
| `components/` | planned | Deep dives for major subsystems (compiler services, runtime host, capability manager, effect dispatcher, decision engine, continuation store). |
| `deployments/` | planned | Environment-specific blueprints (local dev, staging, production, air-gapped, regulated deployments). |
| `playbooks/` | planned | Incident response, effect-resumption drills, supervisor escalation guides. |
| `diagrams/` | planned | Mermaid/PlantUML sources for architecture diagrams; rendered artifacts may live alongside or in generated docs. |
| `patterns/` | planned | Reusable architectural patterns (agent orchestration, capability attenuation, continuation tiering). |

Create a subdirectory only after drafting its local guidance and README.

## Authoring Standards
1. **Front Matter**
   ```/dev/null/architecture_doc_front_matter.md#L1-8
   Title: <document title>
   Authors: <maintainers>
   Status: {Draft|In Review|Active|Archived}
   Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
   Last Updated: <ISO date>
   Summary: <2-3 sentence overview>
   Dependencies: <related RFCs/issues>
   ```
2. **Narrative Voice**  
   - Use precise, implementation-aware prose aimed at senior engineers.  
   - Embed normative language (“MUST”, “SHOULD”) when documenting requirements.

3. **Traceability**  
   - Cross-link to relevant spec clauses, RFCs, packages, and benchmarks.  
   - Reference roadmap milestones in `docs/spec/roadmap.dm` for each commitment.

4. **Diagrams and Assets**  
   - Prefer text-based diagrams (Mermaid, PlantUML).  
   - Store source files under `diagrams/`; link rendered outputs via relative paths.  
   - Provide alt text and captions summarizing architectural insights.

5. **Operational Context**  
   - Capture assumptions about capabilities, network zones, hardware, and model access.  
   - Document failure domains, mitigation strategies, and supervisory hooks for resumable effects.

## Content Lifecycle
1. **Proposal**
   - File an issue outlining scope, motivation, target audience, spec linkage, and acceptance criteria.
   - Identify affected working groups (Runtime, Security, ML Enablement, Developer Experience).

2. **Draft**
   - Produce an outline referencing the Trilogy and any in-flight RFCs.
   - Gather input from component owners; note open questions and risks.

3. **Review**
   - Schedule cross-WG review sessions; log feedback in the document’s discussion section.
   - Update decision tables and trade-off analyses based on review outcomes.

4. **Publish**
   - Merge with changelog entry referencing impacted milestones and packages.
   - Notify stakeholders via release notes or architecture channel summary.

5. **Maintain**
   - Revisit documents at each roadmap checkpoint.
   - Mark outdated sections with `> **Status:** Outdated – see <link>` and create follow-up issues.
   - Archive superseded documents to `archive/` (planned) with replacement pointers.

## Required Sections for Architecture Documents
- **Context & Goals** — articulate problem statement, success criteria, non-goals.
- **Constraints** — security, regulatory, performance, resiliency, capability limits.
- **System Overview** — high-level topology diagram with capability boundaries.
- **Component Interfaces** — describe contracts (APIs, effect signatures, capability manifests).
- **Data & Continuation Flows** — map how prompts, decisions, and continuations traverse the system.
- **Operational Considerations** — deployment steps, monitoring signals, telemetry requirements.
- **Failure & Recovery** — failure modes, supervisor interactions, resumable effect handling.
- **Security Posture** — capability allocation, attenuation rules, sandbox isolation, audit hooks.
- **Observability** — metrics, logs, traces, and dashboards aligned with benchmarks.
- **Open Questions / Risks** — clearly label unknowns and mitigation plans.

## Review & Approval Matrix
| Change Type | Required Approvals |
| --- | --- |
| Runtime topology or capability flow | Runtime WG + Security WG |
| Compiler-service architecture | Language WG + Runtime WG |
| ML pipeline integration | ML Enablement WG + Runtime WG |
| DevEx tooling architecture | Developer Experience WG + Language WG |
| Deployment blueprint | Runtime WG + Security WG (plus DevOps representative if available) |

Escalate contentious decisions via RFCs before merging.

## Quality Checklist (Pre-Merge)
- [ ] References to `diamond.md`, `diamond2.md`, and `diamond3.md` are current.
- [ ] Capability boundaries and effect handling match the latest spec.
- [ ] Diagrams align with described flows; sources are committed.
- [ ] Continuation storage and resumption paths are documented.
- [ ] Security, observability, and failure analyses are complete or explicitly deferred with owners.
- [ ] Dependencies (packages, scripts, benchmarks) are linked.
- [ ] Changelog entry created; roadmap milestones updated if scope shifts.

## Contribution Etiquette
- Use relative links and consistent naming (`kebab-case`) for files and directories.
- Document assumptions and trade-offs; avoid hand-waving around feasibility.
- Keep “Open Questions” near the top for async reviewers.
- Encourage iterative refinement—log TODOs with owner and due date.
- Avoid embedding binaries; reference external storage with access notes.

## Planned Enhancements
- Introduce `architecture.yaml` index summarizing documents, owners, status, and review cadence.
- Add CI checks for diagram synchronization (source vs. rendered artifact hashes).
- Establish architecture decision log integrating with `docs/design-decisions/records/`.
- Build semantic search over architecture docs using the Diamond `<~>` similarity operator once available.
- Automate drift detection against runtime configuration manifests and capability registries.

Maintaining disciplined architecture guidance ensures the Diamond platform translates its crystalline specification into secure, resumable, and semantically grounded operating environments.