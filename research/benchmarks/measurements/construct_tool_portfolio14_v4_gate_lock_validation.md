# v4 Math+Patch Gate-Lock Validation

- Run: `run_20260303_construct_tool_portfolio14_v4_gate_lock`
- Scenario: `research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch`
- CSV: `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`
- Gate model source: `docs/decisions/profile_v1/CONSTRUCT_TOOL_STYLE_GUIDE.md` (Final)

## Final Gates

- Portfolio `net_reduction >= 35%`
- Portfolio `vs_python_with_tools >= 60%`
- Portfolio `tool_overhead <= 15%`
- Per-program `net_reduction >= 5%`
- Per-program `tool_overhead <= 20%`

## Results

| Gate | Threshold | Result | Status |
|---|---:|---:|---|
| Portfolio net_reduction | >= 35% | 40.23% | PASS |
| Portfolio vs_python_with_tools | >= 60% | 65.29% | PASS |
| Portfolio tool_overhead | <= 15% | 7.80% | PASS |
| Per-program net_reduction | >= 5% | fails in 0 programs | PASS |
| Per-program tool_overhead | <= 20% | fails in 0 programs | PASS |

- All gates pass.

## Decision

- **Validated**: `v4_math_patch` is the validated configuration under the final gate model.
- Transition to transpiler phase is approved.
