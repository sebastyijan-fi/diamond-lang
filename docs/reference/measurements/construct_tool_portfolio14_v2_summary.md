# Construct-Tool Portfolio14 v2 (Q1)

- Run: `run_20260303_construct_tool_portfolio14_v2`
- CSV: `research/benchmarks/measurements/construct_tool_portfolio14_v2_q1.csv`
- Scenario: `research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v2`
- Tokenizer: `Qwen/Qwen3-8B` (HF local cache)

## Revised Gates (Locked)

- Per-program floor: `net_reduction >= 15%`
- Portfolio average: `net_reduction >= 40%`
- Portfolio average: `vs_python_with_tools >= 60%`
- Per-program bound: `tool_overhead <= 15%`

## Portfolio Result (All 14 Programs)

- `tool_overhead` (portfolio): `13.35%`
- `net_reduction` (portfolio): `34.12%`
- `vs_python_with_tools` (portfolio): `61.75%`

| Gate | Threshold | Result | Status |
|---|---:|---:|---|
| Per-program `net_reduction` floor | >= 15% | fails in 2 programs | FAIL |
| Portfolio `net_reduction` | >= 40% | 34.12% | FAIL |
| Portfolio `vs_python_with_tools` | >= 60% | 61.75% | PASS |
| Per-program `tool_overhead` cap | <= 15% | fails in 6 programs | FAIL |

## Outliers

- Net floor failures:
  - `05_rate_limiter_token_bucket`: net `0.66%`
  - `09_binary_search`: net `6.90%`
- Tool-overhead cap failures:
  - `02_fibonacci_recursive_iterative`: overhead `33.33%`
  - `03_json_parser_simplified`: overhead `50.00%`
  - `04_url_router`: overhead `16.67%`
  - `05_rate_limiter_token_bucket`: overhead `16.28%`
  - `08_csv_parser`: overhead `28.57%`
  - `09_binary_search`: overhead `17.39%`

## Shape Split

| Group | Count | syntax_reduction | tool_overhead | net_reduction | vs_python_with_tools |
|---|---:|---:|---:|---:|---:|
| strong10 | 10 | 47.39% | 15.73% | 39.12% | 62.99% |
| weak4 | 4 | 26.41% | 8.59% | 20.09% | 58.79% |

## Validation Decision

- **Not validated** under the revised locked gates for this 14-program run.
- Passes one portfolio gate (`vs_python_with_tools`) but fails portfolio `net_reduction` and both per-program gates.
