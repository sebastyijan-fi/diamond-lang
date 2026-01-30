# Security Documentation Guidance

## Purpose
The `docs/security/` workspace codifies how Diamond’s zero-trust, capability-secure architecture is defined, audited, and evolved. Every document must reflect the foundational trilogy:

- `diamond.md` — mandates secure-by-default execution, explicit capabilities, and supervised decision points.
- `diamond2.md` — validates WebAssembly sandboxing, threat models for agentic runtimes, and the synthetic bootstrapping risk posture.
- `diamond3.md` — formalizes capability injection, algebraic effect supervision, and semantic safeguards.

Security documentation ensures implementations, tooling, and ML pipelines preserve Diamond’s crystalline guarantees against adversarial behavior.

---

## Directory Contract
| Subpath | Status | Expected Contents |
| --- | --- | --- |
| `README.md` | present | Orientation, threat model summary, links to specs and policies. |
| `threat-models/` | planned | STRIDE-style analyses, attack trees, and capability abuse scenarios. |
| `policies/` | planned | Capability issuance, key management, disclosure procedures, and verifier access controls. |
| `audits/` | planned | Internal/external audit reports, follow-up tasks, remediation trackers. |
| `playbooks/` | planned | Incident response, continuation quarantine, supervisor escalation procedures. |
| `checklists/` | planned | Pre-flight capability reviews, release security gates, CI/CD hardening steps. |
| `archive/` | planned | Superseded security docs with lineage notes and replacement links. |

Create subdirectories only after drafting a local guidance note and README to keep the workspace coherent.

---

## Authoring Standards

1. **Front Matter**  
   ```/dev/null/security_doc_front_matter.md#L1-8
   Title: <document title>
   Authors: <maintainers>
   Status: {Draft|In Review|Active|Archived}
   Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
   Last Updated: <ISO date>
   Summary: <2-3 sentence overview>
   Dependencies: <RFCs/issues/tools>
   ```

2. **Normative Language**  
   Use RFC 2119 keywords (“MUST”, “SHOULD”, “MAY”) for requirements. Highlight assumptions and scope clearly.

3. **Traceability**  
   - Link to relevant RFCs (`docs/design-decisions/rfcs/`) and decision records.  
   - Reference implementation locations (runtime capability manager, compiler checks, CI scripts).  
   - Tie controls to roadmap milestones in `docs/spec/roadmap.dm`.

4. **Evidence Orientation**  
   - Cite audits, benchmarks, and telemetry sources.  
   - Include verification steps for claims (e.g., “Capability manifests validated via script X”).

5. **Privacy & Compliance**  
   Document handling requirements for sensitive data, ensuring alignment with organizational policies and regional regulations.

---

## Content Lifecycle

1. **Proposal**  
   - Open an issue detailing the security need, affected components, and alignment with the trilogy.  
   - Identify involved working groups (Security, Runtime, Language, ML Enablement, Developer Experience).

2. **Draft**  
   - Produce an outline covering threat mitigations, capability implications, and operational guidance.  
   - Gather input from subsystem owners and incident response leads.

3. **Review**  
   - Conduct peer review sessions; log feedback in `audits/` or `reviews` (planned).  
   - Resolve conflicts through the RFC process when policy or spec changes are required.

4. **Publish**  
   - Merge with an accompanying changelog entry.  
   - Update cross-links (spec, scripts, benchmarks).  
   - Notify stakeholders in the security channel with action items.

5. **Maintain**  
   - Schedule quarterly reviews; label stale sections with `> **Status:** Outdated – see <link>`.  
   - Archive superseded documents after replacements go live.  
   - Track open risks and follow-up tasks via issues.

---

## Required Sections for Security Docs

- **Context & Goals** — problem statement, threat surface, success metrics.  
- **Assumptions & Constraints** — capability boundaries, trust zones, deployment contexts.  
- **Threat Analysis** — attack vectors, likelihood, impact, defensive posture.  
- **Controls & Mitigations** — capability policies, effect supervision, sandbox configuration, verifier guardrails.  
- **Operational Guidance** — monitoring, alerting, rotation cadence, on-call procedures.  
- **Verification & Testing** — fuzzing plans, security benchmarks, regression suites.  
- **Telemetry & Reporting** — metrics, dashboards, log retention, escalation triggers.  
- **Open Issues / Risk Register** — unresolved gaps, owners, and deadlines.

---

## Review & Approval Matrix
| Change Type | Required Approvals |
| --- | --- |
| Capability policy updates | Security WG + Runtime WG |
| Threat model revisions | Security WG + Language WG |
| Incident response playbooks | Security WG + Operations lead |
| Verifier/SLM security changes | Security WG + ML Enablement WG |
| CI/CD hardening procedures | Security WG + Developer Experience WG |

Escalate contentious changes through formal RFCs before merge.

---

## Quality Checklist (Pre-Merge)

- [ ] References to `diamond.md`, `diamond2.md`, and `diamond3.md` are current.  
- [ ] Threat scenarios address capability abuse, prompt injection, semantic verifier evasion.  
- [ ] Controls map to concrete implementation artifacts (runtime modules, scripts, workflows).  
- [ ] Resumable effect handling incorporates quarantine and supervisor intervention.  
- [ ] Telemetry and alerting requirements are defined or marked TBD with owner + due date.  
- [ ] Changelog and roadmap updates included when scope shifts.  
- [ ] Incident response contacts and escalation paths documented.

---

## Contribution Etiquette

- Use relative links and consistent naming (`kebab-case`).  
- Keep “Open Questions” near the top for asynchronous reviews.  
- Annotate TODOs with owner and deadline (`TODO(security-wg, 2024-12-15): audit continuation store encryption`).  
- Avoid embedding sensitive data; reference secure storage locations instead.  
- Summarize decisions succinctly and link to supporting evidence.

---

## Planned Enhancements

- Security control matrix mapped to benchmarks and CI checks.  
- Automated validation for capability manifest schemas and policy documents.  
- Integration with incident management tooling for playbook synchronization.  
- Semantic search index over security docs using Diamond’s `<~>` similarity semantics.  
- Regular “red team” report templates and postmortem guidelines.

---

Maintaining disciplined security documentation ensures Diamond’s capability-secure, effect-resilient, and intent-aware architecture remains defensible against adversarial agents while staying faithful to the project’s crystalline principles.