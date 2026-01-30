# Decision Records Guidance

## Purpose
The `docs/design-decisions/records/` directory archives finalized design decisions for the Diamond language, runtime, and ecosystem. Each record represents a concluded decision-making process—capturing the outcome, rationale, alternatives considered, and implementation implications. All records must trace their lineage to the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and zero-trust execution.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, and module-level capability injection.

Decision records provide institutional memory—ensuring that future contributors understand not just *what* was decided, but *why*.

---

## Directory Contract

| Path | Purpose |
| --- | --- |
| `YYYYMM-<slug>.md` | Individual decision records with date prefix. |
| `index.yaml` (planned) | Machine-readable index of all records with metadata. |
| `README.md` (planned) | Overview of record format and navigation guide. |
| `GUIDANCE.md` | This file—authoring standards and lifecycle rules. |

---

## Record Naming Convention

Use the format: `YYYYMM-<descriptive-slug>.md`

**Examples:**
- `202501-continuation-serialization-format.md`
- `202502-square-bracket-generics.md`
- `202503-capability-manifest-schema.md`

The date prefix indicates when the decision was finalized, enabling chronological sorting.

---

## Required Front Matter

Every decision record must begin with:

```yaml
---
Title: <Descriptive decision title>
Decision-ID: DR-NNNN
Status: Accepted | Rejected | Superseded
Date-Accepted: YYYY-MM-DD
Authors:
  - <name or handle>
Reviewers:
  - <working group or individual>
Spec-Alignment:
  - diamond.md §<section>
  - diamond2.md §<section>
  - diamond3.md §<section>
Related-RFCs:
  - YYYYMM-<rfc-slug>.md
Supersedes: <previous DR-ID or "None">
Superseded-By: <future DR-ID or "None">
Implementation-Status: Pending | In-Progress | Complete
Summary: >
  One to three sentences describing the decision and its impact.
---
```

---

## Record Structure

### 1. Context & Background
- What problem or question prompted this decision?
- What prior art, constraints, or dependencies influenced it?
- Reference relevant spec sections and prior discussions.

### 2. Decision
- State the decision clearly and unambiguously.
- Use RFC 2119 language (MUST, SHOULD, MAY) for normative statements.
- Include code examples or diagrams where clarifying.

### 3. Rationale
- Why was this option chosen over alternatives?
- What evidence supported this choice (benchmarks, prototypes, research)?
- What trade-offs were accepted?

### 4. Alternatives Considered
- List alternatives that were evaluated.
- Explain why each was rejected.
- Note any conditions under which alternatives might be revisited.

### 5. Consequences
- What follows from this decision?
- Positive outcomes and benefits.
- Negative implications or technical debt incurred.
- Future work or open questions deferred.

### 6. Implementation Notes
- Affected components and packages.
- Migration or breaking change considerations.
- Testing and validation requirements.
- Timeline and ownership if applicable.

### 7. References
- Links to RFCs, issues, PRs, external resources.
- Citations for academic papers or prior art.

---

## Record Lifecycle

### Creation
1. An RFC reaches consensus in the `rfcs/` directory.
2. The RFC author (or delegated party) creates a decision record.
3. Copy relevant content from the RFC; add decision-specific sections.
4. Assign a unique Decision ID (DR-NNNN, sequential).
5. Set status to `Accepted` (or `Rejected` for declined proposals).

### Updates
- Decision records are **immutable once accepted**.
- Corrections are made via addenda (new sections) with timestamps.
- Substantial changes require a new decision that supersedes the original.

### Supersession
When a decision is replaced:
1. Update original record's `Superseded-By` field.
2. New record's `Supersedes` field references the original.
3. Add note at top of original: `> **Note:** This decision has been superseded by [DR-XXXX](link).`

### Archival
Records remain in `records/` indefinitely. For major reorganizations:
- Move to `archive/` subdirectory if needed.
- Maintain redirects or cross-references.

---

## Quality Standards

### Clarity
- Write for future readers who weren't part of the discussion.
- Avoid jargon without definition.
- Be specific about what changed and what didn't.

### Completeness
- Include enough context to understand the decision standalone.
- Reference but don't duplicate lengthy RFC content.
- Link to all relevant artifacts (issues, PRs, benchmarks).

### Neutrality
- Present alternatives fairly, even rejected ones.
- Acknowledge trade-offs honestly.
- Separate facts from opinions.

---

## Review Requirements

| Record Type | Required Approvals |
| --- | --- |
| Language/grammar decisions | Language WG lead |
| Runtime/effects decisions | Runtime WG lead |
| Security/capability decisions | Security WG lead |
| Tooling/DX decisions | DX WG lead |
| Cross-cutting decisions | Multiple WG leads |

Records should be reviewed for accuracy, completeness, and alignment with the specification trilogy before merging.

---

## Quality Checklist (Pre-Merge)

- [ ] Front matter is complete and accurate.
- [ ] Decision ID is unique and sequential.
- [ ] RFC linkage is correct (if applicable).
- [ ] All required sections are present.
- [ ] Alternatives are documented fairly.
- [ ] Implementation status reflects reality.
- [ ] Spec alignment references are valid.
- [ ] Supersession chain is correct (if applicable).
- [ ] Writing is clear and self-contained.
- [ ] All reviewers have approved.

---

## Index Maintenance (Planned)

An `index.yaml` will provide machine-readable access to records:

```yaml
records:
  - id: DR-0001
    title: "Continuation Serialization Format"
    file: "202501-continuation-serialization-format.md"
    status: Accepted
    date: 2025-01-15
    tags: [runtime, continuations, serialization]
    
  - id: DR-0002
    title: "Square Bracket Generics"
    file: "202502-square-bracket-generics.md"
    status: Accepted
    date: 2025-02-01
    tags: [language, syntax, generics]
```

This enables automated documentation generation and decision tracking.

---

## Future Enhancements

- Automated validation of front matter and cross-references.
- Decision graph visualization showing supersession chains.
- Integration with changelog generation.
- Search functionality across decision rationales.
- Templates for different decision categories.
- AI-assisted decision drafting with spec alignment checks.

---

Decision records are Diamond's governance memory. Every record should empower future contributors to understand the project's evolution and make informed decisions that honor established principles while enabling progress.