# Construct-Tool Portfolio14 v4 (Math + Patch)

Superseded by gate-lock run:
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_validation.md`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`

- Run: `run_20260303_construct_tool_portfolio14_v4_math_patch`
- Scenario: `research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch`
- CSV: `research/benchmarks/measurements/construct_tool_portfolio14_v4_math_patch_q1.csv`
- Includes:
  - math constructs on `09` and `10` (`$` midpoint, `l()/r()` half-split intrinsics)
  - record patch `x{k:v}` on `07`, `11`, `15`
  - proposals `3+4` retained from `v3.4`

## Portfolio Totals

- `syntax_reduction`: `44.55%`
- `tool_overhead`: `12.07%`
- `net_reduction`: `37.86%`
- `vs_python_with_tools`: `63.91%`

## Gate Status (Revised Model)

| Gate | Threshold | Result | Status |
|---|---:|---:|---|
| Per-program `net_reduction` | >= 15% | fails in 1 programs | FAIL |
| Portfolio `net_reduction` | >= 40% | 37.86% | FAIL |
| Portfolio `vs_python_with_tools` | >= 60% | 63.91% | PASS |
| Per-program `tool_overhead` | <= 15% | fails in 5 programs | FAIL |

- Net floor failures: 05_rate_limiter_token_bucket
- Tool-overhead failures: 02_fibonacci_recursive_iterative, 03_json_parser_simplified, 04_url_router, 05_rate_limiter_token_bucket, 08_csv_parser

## Shape Split

| Group | net_reduction | vs_python_with_tools | tool_overhead |
|---|---:|---:|---:|
| strong10 | 40.56% | 63.87% | 14.55% |
| weak4 | 30.25% | 64.03% | 6.55% |

## Interpretation

- Combined math+patch improves portfolio net materially vs `v3.4`, but still below 40%.
- Value metric remains strong and improving (`vs_python_with_tools` > 60%).
- Remaining blockers are concentrated in non-optimized strong programs (`02`, `03`, `05`) and one per-program net outlier (`05`).

## Gate Adjustment Simulation

If portfolio `net_reduction` gate is relaxed from `>= 40%` to `>= 35%`:

- Portfolio `net_reduction`: `37.86%` -> PASS
- Portfolio `vs_python_with_tools`: `63.91%` -> PASS

Per-program hard gates would still fail due outliers (`05` net floor; `02/03/04/05/08` overhead cap).
