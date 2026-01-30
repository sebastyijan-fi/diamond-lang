# Specification Archive Guidance

## Purpose
The `docs/spec/archive/` directory preserves superseded versions of the Diamond specification manuscripts. Every document stored here must remain traceable to its active successor and should document the historical rationale behind its retirement. Archival records protect institutional memory while preventing outdated guidance from drifting into production use.

## Scope
The archive holds immutable snapshots of:
- `diamond.md` — the Crystal Protocol.
- `diamond2.md` — Architectural Feasibility analysis.
- `diamond3.md` — Semantic Specification.

No other files should be placed here without approval from the Language and Runtime working groups.

## When to Archive
Archive a manuscript when all of the following are true:
1. A revised edition is merged into `docs/spec/` with an approved RFC.
2. All implementation- and roadmap-impacting changes are documented in the changelog.
3. Downstream teams (compiler, runtime, ML enablement, developer experience) have acknowledged the update.

## Archival Process
1. **Freeze** — Copy the outgoing manuscript into this directory before the new edition is merged.
2. **Annotate** — Prepend an archival header (see below) documenting:
   - Replacement version and link.
   - RFC or decision record authorizing the change.
   - Effective date (ISO-8601).
   - Summary of the deltas (1–3 bullet points).
3. **Link** — Update the active manuscript to reference the archived version for historical context.
4. **Communicate** — Notify working groups and tooling owners that the archival snapshot is available.

## Required Header Format
```/dev/null/archive_header.md#L1-6
> **Status:** Archived — superseded by `docs/spec/<file>.md` (version <vX.Y>)
> **Effective Date:** YYYY-MM-DD
> **Authorizing RFC:** docs/design-decisions/rfcs/<id>.md
> **Summary of Changes:**
> - …
> - …
```

## Maintenance Expectations
- Do not edit archived manuscripts beyond correcting the archival header.
- If an archived document is referenced in new work, clearly label it as historical context only.
- Periodically (at least annually) inventory the archive to ensure every entry has a corresponding active successor.
- If a rollback is required, copy the archived manuscript back into `docs/spec/`, update metadata, and follow the normal review process.

## Compliance Checklist
Before archiving:
- [ ] Replacement manuscript merged with approvals.
- [ ] Archival header added and accurate.
- [ ] Links and changelog entries updated.
- [ ] Stakeholders informed (Language, Runtime, Security, ML, DX).

Treat the archive as read-only history that shields contributors and autonomous agents from relying on outdated semantics while preserving the evolution of Diamond’s crystalline intent.