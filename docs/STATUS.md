# Status

Snapshot: 2026-03-04

Current status-reset baseline:
- This working tree is treated as the project’s current status quo baseline for publication work.
- Legacy guidance/docs and obsolete package surface files are intentionally not part of the normative baseline when they are no longer linked from the canonical entrypoints.
- Workspace cleanup milestone was applied: local test cache (`.pytest_cache`) removed from the root.

Current source of truth:
- Completeness inventory report: `docs/completeness/STATUS_REPORT.md`
- Canonical V1 contracts: `docs/decisions/profile_v1/*.md` and `*.json` policy files

What is stable (high level):
- Parser + language-agnostic IR pipeline is in `src/transpiler/`.
- Executable backends exist for Python/JS/Rust (WASM currently parity-mode via JS lowering).
- Semantic validation + capability validation + conformance suites are integrated.
- V1 policy gates exist for safety, capability model, evolution/migration, interop, equality/identity/hash, and module dependency cycles/order.

Quality/certification posture:
- CI gate runner is in `scripts/ci/validate_v1_gates.sh`.
- Stdlib conformance suite is in `src/conformance/`.
- Real-repo certification materials are in `certification/real-repos/`.
- Pre-Rust certification summary: `certification/real-repos/REAL_REPO_CERTIFICATION_2026-03-03.md`.

Research posture:
- Token-economics and construct-tool measurements are in `research/benchmarks/`.
- Decision and policy records are in `docs/decisions/profile_v1/`.

Important:
- Historical or exploratory docs are not normative.
- If two docs disagree, prefer `*_V1.md` contracts plus machine-validated policy JSON + CI gates.

If you are new:
- Follow `START_HERE.md` and ignore deep references until needed.
