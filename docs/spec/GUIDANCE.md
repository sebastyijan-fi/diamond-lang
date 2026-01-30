# Specification Workspace Guidance

## Purpose
The `docs/spec/` directory is the authoritative definition of the Diamond language and runtime. Every document here must preserve the core commitments articulated in the foundational trilogy:

- `diamond.md` — crystallizes the language philosophy, agentic decision model, and capability discipline.
- `diamond2.md` — validates architectural feasibility, synthetic bootstrapping, and runtime security guarantees.
- `diamond3.md` — formalizes grammar, semantic typing, algebraic effects, and capability injection rules.

Updates in this folder set the contract for every compiler, runtime, tooling, and ML initiative in the project.

---

## Directory Structure & Ownership

| File / Subpath        | Owner Working Groups                         | Description |
|-----------------------|----------------------------------------------|-------------|
| `overview.md`         | Language, Runtime                            | Narrative summary of the language goals, design mandates, and positioning relative to existing ecosystems. |
| `grammar.md`          | Language                                     | Formal syntax specification, layout rules, token definitions, and decision operator semantics. |
| `types.md`            | Language, ML Enablement                      | Structural and semantic type system, refinement clauses, verifier integration patterns. |
| `effects.md`          | Language, Runtime                            | Algebraic effect hierarchy, handler semantics, continuation lifecycle, resumability guarantees. |
| `capabilities.md`     | Runtime, Security                            | Object-capability model, module-level injection, attenuation rules, manifest schema. |
| `runtime.md`          | Runtime, Security                            | Execution environment, WebAssembly component model integration, capability manager, decision engine architecture. |
| `roadmap.dm`          | Cross-WG (All)                               | Milestones, acceptance criteria, and temporal commitments for delivering specification features. |
| `archive/`            | Cross-WG (All)                               | Superseded drafts of the three core manuscripts; kept for historical reference. |

Any additional files require a proposal and explicit owner assignment before creation.

---

## Authoring Standards

1. **Front Matter**  
   Each spec document begins with metadata: title, authors, version, status, alignment references (sections from the trilogy), last updated date, and summary.

2. **Formal Voice**  
   Write in precise, implementation-ready language. Avoid aspirational marketing prose; prefer RFC-style rigor.

3. **Deterministic Structure**  
   - Break content into clearly scoped sections reflecting grammar → semantics → runtime expectations.
   - Provide normative statements (“MUST”, “SHOULD”, “MAY”) consistent with RFC 2119 conventions.

4. **Cross-Linking**  
   - Reference related sections across spec documents using relative links.
   - Tie each requirement to the relevant roadmap milestone and implementation artifact (compiler module, runtime component, benchmark).

5. **Executable Alignment**  
   - Include canonical `.dm` snippets only when they compile under the current grammar rules.
   - Flag provisional examples with `> **Status:** Draft – awaiting implementation` and open tracking issues.

6. **Change Tracking**  
   - Summarize substantive edits in `CHANGELOG.md`.
  - Maintain a “History” appendix noting issue/RFC numbers, decision dates, and reviewers.

---

## Change Control Workflow

1. **Proposal Initiation**
   - Open an issue describing the change scope, impacted documents, and relationship to the trilogy.
   - Draft or reference an RFC in `docs/design-decisions/rfcs/`.

2. **Review Requirements**
   - Language semantics changes: Language WG + Runtime WG approval.
   - Capability/security changes: Runtime WG + Security WG approval.
   - Semantic type / verifier changes: Language WG + ML Enablement WG approval.
   - Roadmap updates: Consensus from all affected working groups.

3. **Validation**
   - Run spec lint checks (front matter validation, link integrity, terminology consistency) locally.
   - Ensure supporting tests, benchmarks, or prototype implementations exist or have planned delivery dates.

4. **Merge Criteria**
   - Approved RFC linked in the PR.
   - All feedback resolved with traceable commits or follow-up issues.
   - Changelog entry specifying impact and milestone.

---

## Quality Checklist (Pre-Merge)

- [ ] Preserves philosophical and architectural intent from `diamond.md` and `diamond2.md`.
- [ ] Enforces grammar, effect, and capability rules consistent with `diamond3.md`.
- [ ] Documents security implications and capability boundaries.
- [ ] Defines resumability behavior for any effect or runtime change.
- [ ] Provides telemetry or benchmark expectations, or marks them as TBD with owner + due date.
- [ ] Includes up-to-date references to tooling, runtime, and ML components.
- [ ] Updates `roadmap.dm` milestones or acceptance criteria when scope shifts.

---

## Governance & Maintenance

- **Quarterly Audits**: Each working group reviews relevant documents for accuracy against the latest code and benchmarks.
- **Archive Policy**: Superseded manuscripts move to `archive/` with a deprecation notice and replacement link.
- **Incident Response**: Security-critical changes require immediate addenda describing mitigations and timelines.
- **Backwards Compatibility**: Every normative modification must include guidance on the impact to existing `.dm` code, compiler artifacts, and runtime behaviors.

---

## Planned Enhancements

- Automated spec linting in CI (front matter, cross-links, terminology).
- Spec-to-tests linkage ensuring code examples are exercised in compiler regression suites.
- Semantic diff tooling to detect drift between spec and implementation.
- Structured spec index for LLM-assisted navigation aligned with Diamond’s `<~>` similarity operator.

---

Maintaining a disciplined specification ensures every layer of the Diamond ecosystem—language, runtime, tooling, and ML models—remains aligned with the project’s crystalline intent. Treat `docs/spec/` as the single source of truth for all normative behavior.