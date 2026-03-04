# Publishability Checklist

This repo is publishable when all items below are satisfied:

- [x] Canonical docs entrypoints exist and are linked from `README.md`.
- [x] Non-normative historical material is clearly separated from normatively implemented policy.
- [x] Legacy command entrypoints are preserved as compatibility shims with canonical wrappers in `scripts/certification`.
- [x] Contributor onboarding points to `docs/completeness/STATUS_REPORT.md` and V1 contracts.
- [ ] `.github/` docs/CI and release metadata are aligned to visible source (no hidden/manual drift).
- [x] No dangling canonical references for normative policy files at key publication entry points (manual link scan completed; fixed `RELEASE.md` reference).
- [ ] Project intent and structure are understandable without reading legacy notes.

## Publication baseline (minimum)

If you are preparing a public release tag:

1. Confirm all links in:
   - `README.md`
   - `docs/START_HERE.md`
   - `docs/INDEX.md`
   - `docs/PROJECT_STRUCTURE.md`
   - `docs/REFERENCE_MAP.md`
2. Confirm `.gitignore` excludes generated/build/test artifacts.
3. Confirm `docs/completeness/STATUS_REPORT.md` has the intended release scope (`implemented`/`intentionally_excluded`/`gap`).

Keep this checklist updated with any future structural changes.
