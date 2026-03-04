# Construct-Tool Gate Summary (Q1, Legacy Scenario Gates)

Legacy gates used for the initial 4-program scenario comparisons:
- tool_overhead <= 15%
- net_reduction >= 40%
- vs_python_with_tools >= 60%

| Scenario | tool_overhead | net_reduction | vs_python_with_tools | Gate Result |
|---|---:|---:|---:|---|
| fn_layer | 12.56% | 54.47% | 70.29% | PASS |
| fn_error | 25.63% | 49.19% | 65.47% | FAIL |
| fn_error_compose | 16.08% | 53.05% | 68.09% | FAIL |
| fn_error_compose_v2 | 13.57% | 54.06% | 68.78% | PASS |

## Locked Revision

The gate model is now locked in `docs/decisions/profile_v1/CONSTRUCT_TOOL_STYLE_GUIDE.md`:

- Per-program floor: `net_reduction >= 15%`
- Portfolio average: `net_reduction >= 40%`
- Portfolio average: `vs_python_with_tools >= 60%`
- Per-program bound: `tool_overhead <= 15%`

Portfolio evaluation artifact:

- `docs/reference/measurements/construct_tool_portfolio14_v2_summary.md`

## Totals by Scenario

| Scenario | python | python_with_tools | diamond_base | diamond_full |
|---|---:|---:|---:|---:|
| fn_layer | 492 | 754 | 199 | 224 |
| fn_error | 492 | 724 | 199 | 250 |
| fn_error_compose | 492 | 724 | 199 | 231 |
| fn_error_compose_v2 | 492 | 724 | 199 | 226 |
