# Design Decision Templates Guidance

## Purpose
The `docs/design-decisions/templates/` directory provides standardized templates for governance documents within the Diamond project. These templates ensure consistency, completeness, and alignment with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and security posture.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, and module-level capability injection.

Well-designed templates accelerate decision-making by encoding best practices and required considerations into document structure.

---

## Directory Contract

| Template | Purpose | Use When |
| --- | --- | --- |
| `rfc-template.md` | Request for Comments template | Proposing normative changes to language, runtime, or tooling |
| `decision-record-template.md` | Architecture Decision Record (ADR) | Recording accepted/rejected decisions with rationale |
| `meeting-notes-template.md` | Working Group meeting notes | Documenting synchronous discussions |
| `security-review-template.md` | Security review checklist | Evaluating capability and security implications |
| `api-design-template.md` | API design document | Proposing new public APIs |
| `retrospective-template.md` | Milestone retrospective | Reflecting on completed work phases |

Templates should be updated as governance processes evolve.

---

## Template Design Principles

### 1. Mandatory Front Matter
Every template must include structured metadata:

```markdown
---
Title: <document title>
Authors: <comma-separated names>
Status: {Draft|Review|Accepted|Rejected|Superseded}
Created: <ISO date>
Last Updated: <ISO date>
Spec Alignment: diamond.md §#, diamond2.md §#, diamond3.md §#
Working Groups: <Language|Runtime|Security|ML Enablement|Developer Experience>
Related Documents: <links or "None">
---
```

### 2. Required Sections
Templates should prompt authors to address:

- **Context & Motivation**: Why is this document needed?
- **Proposal/Decision**: What specifically is being proposed or decided?
- **Alignment with Spec Trilogy**: How does this relate to the three core manuscripts?
- **Capability & Effect Implications**: Security and effect system impact.
- **Alternatives Considered**: What other options were evaluated?
- **Open Questions**: Unresolved issues requiring input.
- **Implementation Plan**: Concrete next steps with owners.

### 3. Instructional Comments
Include HTML comments with guidance for authors:

```markdown
<!-- 
  Describe the problem you're solving. 
  Reference specific issues, user feedback, or specification gaps.
  Keep this section concise (2-3 paragraphs).
-->
```

### 4. Checklists for Completeness
Include quality checklists that authors must complete:

```markdown
## Pre-Submission Checklist

- [ ] Front matter is complete and accurate
- [ ] Spec alignment references verified
- [ ] Capability implications documented
- [ ] Effect system impact assessed
- [ ] Security considerations addressed
- [ ] Implementation plan includes owners and deadlines
- [ ] Reviewers identified from relevant working groups
```

---

## Template Maintenance

### Creating New Templates

1. Identify a recurring document type that would benefit from standardization.
2. Draft the template with required sections and instructional comments.
3. Review with relevant working groups.
4. Add to this directory with appropriate naming.
5. Update this GUIDANCE.md to include the new template.

### Updating Templates

1. Propose changes via PR with rationale.
2. Consider backward compatibility with existing documents.
3. Update GUIDANCE.md if template purpose changes.
4. Announce significant changes to working groups.

### Template Versioning

Templates evolve with the project. Include a version header:

```markdown
<!-- Template Version: 1.2 | Last Updated: 2025-01-15 -->
```

Documents created from templates should note the template version used.

---

## RFC Template Structure

The RFC template is the most critical template. It should include:

```markdown
# RFC-NNNN: <Title>

<!-- Template Version: 1.0 -->

## Metadata
- **Authors**: 
- **Status**: Draft
- **Created**: YYYY-MM-DD
- **Spec Alignment**: diamond.md §, diamond2.md §, diamond3.md §
- **Working Groups**: 

## Summary
<!-- 2-3 sentence overview of the proposal -->

## Motivation
<!-- Why is this change needed? What problem does it solve? -->

## Alignment with Specification Trilogy
<!-- How does this relate to diamond.md, diamond2.md, diamond3.md? -->

## Detailed Design
<!-- Technical details of the proposal -->

### Grammar Changes (if applicable)
<!-- Any syntax modifications -->

### Type System Impact
<!-- Effects on type checking and inference -->

### Effect System Impact
<!-- Changes to algebraic effects or handlers -->

### Capability Implications
<!-- Security and capability model changes -->

## Alternatives Considered
<!-- Other approaches and why they were rejected -->

## Security Considerations
<!-- Threat analysis, mitigations, capability changes -->

## Implementation Plan
<!-- Milestones, owners, dependencies, timeline -->

## Open Questions
<!-- Unresolved issues requiring community input -->

## Changelog
<!-- Track revisions to this RFC -->

## Pre-Submission Checklist
- [ ] Summary is clear and concise
- [ ] Motivation explains the problem
- [ ] Spec alignment verified
- [ ] Security implications addressed
- [ ] Implementation plan is actionable
- [ ] Reviewers assigned
```

---

## Decision Record Template Structure

For recording accepted or rejected decisions:

```markdown
# ADR-NNNN: <Decision Title>

## Status
{Accepted|Rejected|Superseded by ADR-XXXX}

## Date
YYYY-MM-DD

## Context
<!-- What prompted this decision? -->

## Decision
<!-- What was decided? -->

## Rationale
<!-- Why was this decision made? -->

## Consequences
<!-- What are the implications? -->

## Spec Alignment
<!-- References to specification trilogy -->

## Related Documents
<!-- Links to RFCs, issues, PRs -->
```

---

## Quality Standards for Templates

### Clarity
- Use plain language; avoid jargon where possible.
- Define terms specific to Diamond.
- Provide examples in instructional comments.

### Completeness
- Cover all aspects required for informed decision-making.
- Include security, capability, and effect considerations.
- Prompt for implementation details.

### Consistency
- Use consistent heading levels and naming.
- Align checkbox formats and metadata fields.
- Follow Markdown style guide.

### Actionability
- Checklists should be directly usable.
- Implementation sections should be concrete.
- Open questions should be specific.

---

## Quality Checklist for This Directory

- [ ] Each template has clear purpose and usage guidance.
- [ ] Templates include all mandatory sections.
- [ ] Instructional comments help authors fill in sections.
- [ ] Quality checklists are actionable.
- [ ] Template versioning is documented.
- [ ] This GUIDANCE.md is kept current with available templates.

---

## Future Enhancements

- Template linting in CI to validate structure.
- Auto-generation of document IDs (RFC numbers, ADR numbers).
- Template wizard CLI tool for scaffolding documents.
- Integration with documentation portal for discoverability.
- AI-assisted template filling with spec-aware suggestions.

---

Well-crafted templates reduce cognitive load, ensure consistency, and encode institutional knowledge. Every template in this directory should make governance easier while maintaining Diamond's standards for clarity, security, and spec alignment.