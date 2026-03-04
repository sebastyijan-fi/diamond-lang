# Construct-Tool Style Guide (v1)

Purpose: hard token ceilings for construct-tool composition, derived from measured passing runs.

Primary passing references:
- `run_20260303_construct_tool_fn_layer`
- `run_20260303_construct_tool_fn_error_compose_v2`

## Global Gates (Final)

- Portfolio `net_reduction >= 35%`
- Portfolio `vs_python_with_tools >= 60%`
- Portfolio `tool_overhead <= 15%`
- Per-program `net_reduction >= 5%`
- Per-program `tool_overhead <= 20%`

Enforcement:
- Per-program gates apply to each measured program row.
- Portfolio gates apply to the aggregate `TOTAL` row across the benchmark set.

Rationale:
- Portfolio metrics capture real codebase value.
- Per-program floors remain as guardrails against pathological regressions.
- Per-program overhead cap is relaxed for small-program fixed-cost fairness, while portfolio overhead remains strict.

Validated reference:
- `run_20260303_construct_tool_portfolio14_v4_gate_lock`
- Scenario: `research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch`

## Derived Construct Ceilings (from v2)

Measured from 4 strong programs (`01,04,08,16`):

- Function-layer incremental overhead:
  - `+25` tokens total over base
  - `5` function defs in scenario
  - ceiling: `<= 5 tokens / function definition`

- Error-layer incremental overhead (on top of function layer):
  - `+2` tokens total over function-layer full
  - `2` explicit propagation sites (`call)?`)
  - ceiling: `<= 1 token / propagation site`

- Shared composition overhead:
  - observed near `0` additional tokens after shared encoding in v2
  - ceiling: `<= 0.5 tokens / function` (practical upper bound)

## Composition Pattern Rules (required)

1. Encode function-layer metadata in one shared compact marker.
   - Keep one marker block per function header.

2. Encode error layer via propagation points, not repeated context wrappers.
   - Prefer `call)?` style markers at selected boundaries.
   - Avoid repeating explicit error context blocks at each branch.

3. Do not duplicate trace/capability markers inside bodies.
   - Function header carries shared tool context.

4. Keep error propagation sparse and strategic.
   - boundary calls and recursive edges first.
   - avoid blanket annotation of every expression.

5. Use tool-header inheritance in helper clusters.
   - Emit one explicit tool header on the entry declaration.
   - Omit repeated headers on subsequent helper declarations in the same group.
   - Re-emit explicitly when changing tool context.

6. Inline single-use pure helpers where it reduces tokens.
   - Apply only to expression-pure helpers.
   - Preserve grouping with parentheses for nested ternaries/comparisons.
   - Do not inline helpers that encapsulate boundary effects or error-context boundaries.

## Construct-Level Gate Checks

For each new construct tool layer (loop, branch, boundary, module):

- Measure added tokens per occurrence.
- Reject if any layer exceeds its ceiling in aggregate tests.
- Reject if combined layers push scenario `tool_overhead` over `15%`.

## Weak-Shape Policy

Weak-shape stress and portfolio runs show that tight algorithmic forms can miss net floors even when overhead stays bounded.

Policy:
- Treat performance as shape-dependent.
- Optimize portfolio-level outcomes first, while preserving per-program safety floors.
- Use tiered profiles by shape where needed:
  - `full_tool_profile` for high-compression shapes
  - `lite_tool_profile` for weak-compression shapes
