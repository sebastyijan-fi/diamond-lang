# Design Decisions Archive Guidance

## Purpose
The `docs/design-decisions/archive/` directory preserves superseded governance artifacts—RFCs that have been replaced, decisions that have been revised, and historical documentation that remains valuable for understanding Diamond's evolution. All archived content must maintain lineage to the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and security posture.
- **`diamond3.md`** — Grammar, effect semantics, and module-level capability injection.

Archives are not dead documents—they are the institutional memory that informs future decisions.

---

## Directory Contract

| Path | Status | Expectations |
| --- | --- | --- |
| `README.md` | planned | Index of archived items with supersession notes. |
| `rfcs/` | planned | Superseded RFC documents with lineage metadata. |
| `records/` | planned | Replaced decision records with revision history. |
| `meeting-notes/` | planned | Historical meeting notes and discussion summaries. |
| `*.md` | active | Individual archived documents with archival headers. |

Each archived document must include an archival header explaining why it was archived and what replaced it.

---

## Archival Process

### When to Archive

Documents should be moved to the archive when:

1. **Superseded**: A newer RFC or decision replaces the content.
2. **Withdrawn**: The proposal was withdrawn before acceptance.
3. **Obsolete**: Language evolution has made the content irrelevant.
4. **Consolidated**: Multiple documents have been merged into one.

### Archival Procedure

1. **Add Archival Header**: Insert metadata at the top of the document:
   ```markdown
   ---
   Status: Archived
   Archived Date: <ISO date>
   Archived By: <contributor>
   Superseded By: <link to replacement document or "N/A">
   Reason: <Superseded|Withdrawn|Obsolete|Consolidated>
   Original Location: <original path in repository>
   ---
   
   > **⚠️ ARCHIVED**: This document has been superseded. See [replacement](link) for current guidance.
   ```

2. **Move the Document**: Transfer to appropriate archive subdirectory.

3. **Update References**: 
   - Add redirect notes in original location (optional stub file).
   - Update any documents that referenced the archived content.

4. **Update Archive Index**: Add entry to `archive/README.md` (when created).

5. **Preserve Git History**: Use `git mv` to maintain commit history.

---

## Document Format

### Archived RFC Format

```markdown
---
Status: Archived
Archived Date: 2025-06-15
Archived By: @contributor
Superseded By: docs/design-decisions/rfcs/202506-new-effects-model.md
Reason: Superseded
Original Location: docs/design-decisions/rfcs/202501-original-effects.md
---

> **⚠️ ARCHIVED**: This RFC has been superseded by [RFC 202506: New Effects Model](../rfcs/202506-new-effects-model.md).

# [Original RFC Title]

[Original content preserved verbatim below]

---

[Original RFC content...]
```

### Archived Decision Record Format

```markdown
---
Status: Archived
Archived Date: 2025-06-15
Archived By: @contributor
Superseded By: docs/design-decisions/records/DR-042-revised-capability-model.md
Reason: Superseded
Original Location: docs/design-decisions/records/DR-023-initial-capability-model.md
---

> **⚠️ ARCHIVED**: This decision has been revised. See [DR-042](../records/DR-042-revised-capability-model.md) for the current model.

# [Original Decision Title]

[Original content preserved verbatim below]

---

[Original decision record content...]
```

---

## Archive Organization

### By Type
```
archive/
├── rfcs/                    # Superseded RFC documents
│   ├── 202501-*.md
│   └── 202502-*.md
├── records/                 # Replaced decision records
│   ├── DR-001-*.md
│   └── DR-002-*.md
└── meeting-notes/           # Historical discussions
    ├── 2025-01-*.md
    └── 2025-02-*.md
```

### By Reason
Alternatively, organize by archival reason:
```
archive/
├── superseded/              # Replaced by newer versions
├── withdrawn/               # Proposals that were withdrawn
├── obsolete/                # No longer relevant to current design
└── consolidated/            # Merged into other documents
```

---

## Access and Reference

### Citing Archived Documents

When referencing archived documents in current documentation:

```markdown
For historical context, see the [original effects proposal](../archive/rfcs/202501-original-effects.md) 
which was superseded by the current model in [RFC 202506](../rfcs/202506-new-effects-model.md).
```

### Search and Discovery

The archive should support:
- Chronological browsing via date-prefixed filenames.
- Topic search via grep and document metadata.
- Lineage tracking via `Superseded By` links.

---

## Retention Policy

### What to Preserve

- All accepted RFCs that were later superseded.
- All decision records that were revised.
- Meeting notes with significant design discussions.
- Any document that influenced current design decisions.

### What to Exclude

- Draft documents that were never formally proposed.
- Typo fixes or minor editorial corrections.
- Working copies or personal notes.
- Duplicate copies of the same document.

---

## Quality Standards

### Archived Document Requirements

- [ ] Archival header is complete and accurate.
- [ ] Supersession link points to valid replacement (or explains absence).
- [ ] Original content is preserved verbatim (no substantive edits).
- [ ] Git history is preserved via proper move operations.
- [ ] References to this document are updated or annotated.
- [ ] Archive index is updated (when index exists).

### Periodic Review

- Review archive quarterly for broken links and outdated metadata.
- Verify supersession chains are complete and navigable.
- Ensure new archives follow formatting standards.

---

## Use Cases

### Historical Research

Contributors investigating why a design decision was made can trace the lineage:

1. Find current RFC/decision record.
2. Check for `Supersedes` references.
3. Navigate to archived predecessors.
4. Review original rationale and alternatives considered.

### Decision Reversals

If a superseding decision needs to be reversed:

1. Reference the archived document for original reasoning.
2. Create new RFC proposing to revert or modify.
3. Link to both current and archived documents.
4. Archive the superseding document if reversal is accepted.

### Onboarding

New contributors can use the archive to understand:

- How the language evolved.
- Why certain alternatives were rejected.
- The reasoning behind current design choices.

---

## Future Enhancements

- Automated archive index generation from document metadata.
- Lineage visualization showing RFC/decision evolution.
- Search interface for archived documents.
- Integration with release notes to link archived decisions to version history.
- Markdown linting for archival header compliance.

---

The archive is Diamond's institutional memory. Preserve it carefully—future contributors will thank you for maintaining the chain of reasoning that led to the language we're building today.