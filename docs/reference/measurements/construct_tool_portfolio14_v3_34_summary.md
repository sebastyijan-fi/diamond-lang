# Construct-Tool Portfolio14 v3.4 (Proposals 3+4)

- Baseline run: `run_20260303_construct_tool_portfolio14_v2`
- New run: `run_20260303_construct_tool_portfolio14_v3_34`
- Scenario: `research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v3_34`
- Changes applied:
  - Proposal 3: tool-header inheritance on helper declarations (`10`, `16`, `09` full)
  - Proposal 4: inline single-use helper for `09_binary_search` (base + full)

## Portfolio Totals

| Metric | v2 | v3.4 | Delta |
|---|---:|---:|---:|
| diamond_base tokens | 981 | 974 | -7 |
| diamond_full tokens | 1112 | 1086 | -26 |
| syntax_reduction | 41.88% | 42.30% | 0.41% |
| tool_overhead | 13.35% | 11.50% | -1.85% |
| net_reduction | 34.12% | 35.66% | 1.54% |
| vs_python_with_tools | 61.75% | 62.64% | 0.89% |

## Program Impact Highlights

| Program | v2 full | v3.4 full | Delta | v2 net | v3.4 net |
|---|---:|---:|---:|---:|---:|
| 09_binary_search | 108 | 92 | -16 | 6.90% | 20.69% |
| 10_merge_sort | 102 | 97 | -5 | 41.71% | 44.57% |
| 16_retry_exponential_backoff | 116 | 111 | -5 | 39.27% | 41.88% |

## Strong-Program Regression Check

- PASS: no strong-program token regressions (base/full token counts are unchanged or lower).

| Group | net_reduction v2 | net_reduction v3.4 | Delta |
|---|---:|---:|---:|
| strong10 | 39.12% | 39.92% | 0.80% |
| weak4 | 20.09% | 23.70% | 3.61% |

## Revised Gate Status (v3.4)

| Gate | Threshold | Result | Status |
|---|---:|---:|---|
| Per-program `net_reduction` | >= 15% | fails in 1 programs | FAIL |
| Portfolio `net_reduction` | >= 40% | 35.66% | FAIL |
| Portfolio `vs_python_with_tools` | >= 60% | 62.64% | PASS |
| Per-program `tool_overhead` | <= 15% | fails in 5 programs | FAIL |

- Net floor failures: 05_rate_limiter_token_bucket
- Tool-overhead failures: 02_fibonacci_recursive_iterative, 03_json_parser_simplified, 04_url_router, 05_rate_limiter_token_bucket, 08_csv_parser

## Decision

- Proposal 3+4 materially improve weak-shape compression and keep strong programs non-regressing.
- Portfolio improves but still misses the 40% net gate.
- Keep gate unchanged for now; next step is Proposal 1 (record patch) as planned.
