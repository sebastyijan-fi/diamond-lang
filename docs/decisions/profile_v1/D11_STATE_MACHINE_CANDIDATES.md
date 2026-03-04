# D11 Candidate Track: State-Machine Core Primitives

Purpose: unblock direct ports of parser/state-heavy modules (e.g. `tomli/_parser.py`) without violating Diamond v1 design constraints.

Governance:
- `docs/decisions/profile_v1/LANGUAGE_CHANGE_GATE.md`

## Trigger Evidence

- `tomli_probe` reports high parser pressure:
  - loops: `17`
  - exception flow: `60`
  - classes: `5`
  - report: `src/probing/reports/run_20260303T204447Z_probe_tomli_probe.json`

## Constraints

1. Deterministic parse only.
2. No regressions on strong-suite token counts.
3. Portfolio tool gates remain green.
4. Keep core grammar compact.

## Candidate Primitives (to measure)

1. `step` form (single-step state transition)
- Shape: `step(s,e)>S=...`
- Intent: compact explicit state transition unit for parser loops.

2. `loop` form (bounded transition fold)
- Shape: `loop(seq,init,s,e:step_expr)`
- Intent: remove verbose manual fold wiring in state-machine code.

3. `guard` form (error-on-false)
- Shape: `guard(cond,msg,pos)`
- Intent: compact parser guard that lowers to exception context path.

4. `peek/take` string cursor helpers
- Shape: `peek(src,i)`, `take(src,i,n)`
- Intent: canonical cursor semantics for scanners/parsers.

## Measurement Plan

For each candidate:

1. Encode representative parser fragments from `tomli/_parser.py`.
2. Measure token impact vs current Diamond encoding.
3. Run ambiguity checks.
4. Verify transpile + behavior parity on targeted parser cases.
5. Promote only if change-gate passes.

## Status

- State: `proposed`
- Next action: implement candidate A/B syntax samples in `research/benchmarks/hypotheses/` and run tokenbench.
