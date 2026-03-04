# Diamond Core Gap Backlog

Purpose: convert port/probe findings into prioritized core language work items.

Governance reference:
- `docs/decisions/profile_v1/LANGUAGE_CHANGE_GATE.md`

## Current Priority Queue

1. Parser/state-machine direct-port primitives (High)
- Trigger: large parser modules (e.g., `tomli/_parser.py`) remain adapter-heavy.
- Gap class: stateful control-flow ergonomics in expression-dense core.
- Direction: add compact canonical state-machine form that preserves determinism and token efficiency.
- Status: `observed`.

Measured probe pressure:
- `tomli_probe` (`c20c491`): loops `17`, exceptions `60`, classes `5`, yield/gen `2`.
- Report: `src/probing/reports/run_20260303T204447Z_probe_tomli_probe.json`.

2. Class/decorator model for full direct ports (High)
- Trigger: auto probes show heavy class + decorator usage in challenging repos.
- Gap class: object/decorator semantics not first-class in core.
- Direction: define minimal object/decorator lowering profile or canonical Diamond equivalent.
- Status: `observed`.

Measured probe pressure:
- `click_probe` (`cdab890`): classes `78`, decorators `206`.
- `dotenv_probe` (`da0c820`): classes `10`, decorators `34`.
- Report: `src/probing/reports/run_20260303T204519Z_probe_click_probe.json`.
- Report: `src/probing/reports/run_20260303T210236Z_probe_dotenv_probe.json`.

3. Async/concurrency semantics (High)
- Trigger: probes detect async functions/contexts in modern repos.
- Gap class: no first-class async/concurrency semantics in v1 core.
- Direction: evaluate compact `par`/`pipe` semantics with backend-specific lowering.
- Status: `observed`.

4. Context manager/effect boundary model (Medium)
- Trigger: heavy `with` usage in many production repos.
- Gap class: no direct `with` construct in core.
- Direction: effect-boundary primitive that preserves capability/resource tracing semantics.
- Status: `observed`.

5. Generator/yield model (Medium)
- Trigger: generator-heavy libraries.
- Gap class: yield/coroutine semantics not in v1.
- Direction: decide whether to add generator core semantics or canonical desugaring profile.
- Status: `observed`.

Measured probe pressure:
- `click_probe`: yield/gen `56`.
- `dotenv_probe`: yield/gen `13`.

## Recently Closed Probe-Driven Improvements

1. Behavior parity NaN handling
- Fix: behavior equivalence harness now uses NaN-aware deep equality.
- File: `src/transpiler/run_behavior_tests.py`
- Status: `locked`.

2. Probe baseline reliability improvements
- Fix: probe test harness now auto-sets `PYTHONPATH` (`repo` + optional `repo/src`) and records fallback `-k 'not cli'` runs when console-script entrypoints are missing.
- File: `src/probing/probe_repo.py`
- Status: `locked` (tooling infrastructure).
