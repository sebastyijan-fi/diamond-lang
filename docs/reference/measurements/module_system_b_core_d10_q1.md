# D10 B-core Module Metrics (Q1)

Run ids:
- `run_20260303_d10_b_core_dm_v2` (tokenbench on `.dmd`)
- `run_20260303_d10_b_core_py_v2` (tokenbench on Python equivalents)
- `run_20260303_d10_b_core_structure_v2` (derived structure metrics + parse gate)

Tokenizer:
- `Qwen/Qwen3-8B` local `tokenizer.json`

## Per-program metrics

Formulae:
- `structure_overhead = (multiblock_tokens - singlefile_tokens) / singlefile_tokens`
- `tokens_per_edge = overhead_tokens / edge_occurrences`

| Program | multiblock | singlefile | overhead_tokens | structure_overhead | edge_occurrences | unique_edges | tokens_per_edge |
|---|---:|---:|---:|---:|---:|---:|---:|
| `url_parser` | 236 | 222 | 14 | 6.31% | 8 | 2 | 1.75 |
| `key_value_store` | 166 | 155 | 11 | 7.10% | 8 | 2 | 1.38 |
| `event_emitter_handlers` | 155 | 142 | 13 | 9.15% | 8 | 3 | 1.62 |

## Portfolio metrics

- `multiblock_tokens_total`: `557`
- `singlefile_tokens_total`: `519`
- `overhead_tokens_total`: `38`
- `portfolio structure_overhead`: `7.32%`
- `edge_occurrences_total`: `24`
- `portfolio tokens_per_edge`: `1.58`

## Ambiguity gate

- `ambiguity_parse_clean = true`
- Method: block extraction parse + existing declaration parser on every block body.

## Gate status

- `structure_overhead <= 10%` per program: PASS
- `tokens_per_edge <= 2.0` per program: PASS
- `ambiguity = 0` parse clean: PASS
