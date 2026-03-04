# Real-repo certification artifacts

These subfolders contain compatibility checks for representative external repos.

- `tomli/`
- `retry/`
- `dotenv/`
- `iniconfig/`

Keep:
- Upstream test commands and command outputs that demonstrate reproducibility.
- Notes on failure mode handling and expected pass criteria.

If a repo is no longer part of the claimed evidence set, move it to archive.

## Execution model

Canonical certification scripts are stored in `scripts/certification/*`.
Commands shown in repo markdowns under `certification/real-repos/*` are compatibility
entry points that delegate to canonical script locations.
