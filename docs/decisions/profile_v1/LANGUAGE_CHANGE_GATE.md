# Diamond v1 Language Change Gate

Purpose: keep Diamond language quality and identity stable while using ports to discover missing core capabilities.

Core principle:
- Porting is a discovery probe.
- Diamond language quality is the product.

---

## 1) Non-Negotiables (Project Soul)

Any change that violates these is rejected:

1. Token-first optimization remains the primary objective.
2. Grammar remains deterministic and unambiguous.
3. Construct-tool fusion remains the default model.
4. Core grammar stays compact; profile/surface variation belongs in mappings, not semantic churn.

---

## 2) Change Intake (When a Port Finds a Gap)

Every proposed language change must be logged as:

1. Trigger case:
- exact failing repo/program/case.
2. Root cause:
- parser ambiguity, missing semantic primitive, runtime contract gap, or backend-lowering gap.
3. Minimal language delta:
- smallest grammar/IR/runtime change that solves the issue.
4. Adapter fallback:
- temporary shim if needed; must be marked as transitional.

Probe source:
- Automated probe runs (`src/probing/probe_repo.py`) are valid intake signals when tied to concrete reports and measurement log entries.

---

## 3) Promotion Gates (Required to Accept a Change)

A language/core change is promoted only if all pass:

1. Necessity:
- blocks full/direct port path or appears in at least two independent real-code paths.
2. Parse safety:
- no new ambiguities; regression parser suite stays green.
3. Token economics:
- no regressions on locked strong-suite token counts.
4. Tool economics:
- construct-tool portfolio gates remain green.
5. Contract coherence:
- semantic contracts stay backend-independent and testable.
6. Spec budget discipline:
- cold-start complexity remains bounded (no gratuitous rule growth).

---

## 4) Implementation Order

For accepted changes, apply in this order:

1. Semantics contract update (`SEMANTIC_CONTRACTS.md`).
2. Grammar/IR update.
3. Runtime contract + conformance tests.
4. Backend lowering.
5. Remove transitional adapter glue.

No "backend-only semantics patches" without an explicit contract update.

---

## 5) Change States

Use explicit state labels in logs/docs:

1. `observed`:
- gap found, no language change accepted.
2. `proposed`:
- minimal delta drafted with risk and token impact.
3. `provisional`:
- implemented behind tests, not yet lock-promoted.
4. `locked`:
- all promotion gates passed and documented in decision log.

---

## 6) Current Core Focus (v1 -> next)

Priority classes:

1. High:
- semantics that unblock direct full-module ports (state-machine/parser-heavy code),
- error-model and runtime-contract edge coherence.
2. Medium:
- ergonomics that reduce adapter reliance without growing ambiguity.
3. Low:
- convenience syntax that does not unlock new code shapes.

---

## 7) Relation to Existing Artifacts

This gate complements:
- `docs/decisions/profile_v1/DECISION_DEFENSE.md`
- `docs/decisions/profile_v1/SEMANTIC_CONTRACTS.md`
- `docs/decisions/profile_v1/LIMITATIONS.md`
- `research/benchmarks/measurements/decision_log.jsonl`

It does not replace portfolio/token/tool gates; it governs how new language changes are admitted.
