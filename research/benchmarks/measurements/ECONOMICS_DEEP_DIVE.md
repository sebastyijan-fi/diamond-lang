# Diamond Economics Deep Dive (Q1)

This document gives a claim-by-claim economics view of Diamond using only measured records in this repository.

## Executive Result

Final validated portfolio run:
- Run: `run_20260303_construct_tool_portfolio14_v4_gate_lock`
- Totals: Python `1688`, Python+tools `2907`, Diamond base `936`, Diamond full `1009`
- `syntax_reduction`: `44.55%`
- `tool_overhead`: `7.80%`
- `net_reduction`: `40.23%`
- `vs_python_with_tools`: `65.29%`
- Source: `construct_tool_portfolio14_v4_gate_lock_q1.csv`

Capacity interpretation:
- Same token budget vs Python (no tools): `1.67x` semantic capacity (`1 / (1 - 0.402251)`)
- Same token budget vs Python with equivalent tooling: `2.88x` semantic capacity (`1 / (1 - 0.652907)`)

## Metric Definitions

- `syntax_reduction = (python - diamond_base) / python`
- `tool_overhead = (diamond_full - diamond_base) / diamond_base`
- `net_reduction = (python - diamond_full) / python`
- `vs_python_with_tools = (python_with_tools - diamond_full) / python_with_tools`

Primary calculator source:
- `research/benchmarks/tools/construct_tool_bench.py`

## Evidence Timeline

### 1) Syntax-only economics

Measured before full tool-layer composition:

| Experiment | Python | Diamond candidate | Reduction |
|---|---:|---:|---:|
| HTTP compression spectrum (L3 alien vs Python) | 115 | 54 | 53.04% |
| FizzBuzz (C vs Python) | 159 | 48 | 69.81% |
| 5-program suite total (C vs Python) | 776 | 341 | 56.06% |

Source:
- `docs/reference/measurements/observations_q1.md`

### 2) Tool-layer composition economics

Early construct-tool scenarios (4-program set) showed that composition strategy, not tool presence itself, determines budget success:

| Scenario | tool_overhead | net_reduction | vs_python_with_tools | Result |
|---|---:|---:|---:|---|
| `fn_layer` | 12.56% | 54.47% | 70.29% | PASS |
| `fn_error` (naive add) | 25.63% | 49.19% | 65.47% | FAIL |
| `fn_error_compose_v2` | 13.57% | 54.06% | 68.78% | PASS |

Source:
- `docs/reference/measurements/construct_tool_q1_summary.md`

### 3) Portfolio progression (14 programs)

| Run | diamond_base | diamond_full | syntax_reduction | tool_overhead | net_reduction | vs_python_with_tools |
|---|---:|---:|---:|---:|---:|---:|
| `v2` | 981 | 1112 | 41.88% | 13.35% | 34.12% | 61.75% |
| `v3.4` (proposals 3+4) | 974 | 1086 | 42.30% | 11.50% | 35.66% | 62.64% |
| `v4_math_patch` | 936 | 1049 | 44.55% | 12.07% | 37.86% | 63.91% |
| `v4_gate_lock` (validated) | 936 | 1009 | 44.55% | 7.80% | 40.23% | 65.29% |

Sources:
- `research/benchmarks/measurements/construct_tool_portfolio14_v2_q1.csv`
- `research/benchmarks/measurements/construct_tool_portfolio14_v3_34_q1.csv`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_math_patch_q1.csv`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`

### 4) Distribution and floor behavior (final validated run)

Shape split:

| Group | Count | syntax_reduction | tool_overhead | net_reduction | vs_python_with_tools |
|---|---:|---:|---:|---:|---:|
| strong10 | 10 | 48.11% | 8.36% | 43.78% | 65.82% |
| weak4 | 4 | 34.54% | 6.55% | 30.25% | 64.03% |

Outlier bounds:
- Lowest `net_reduction`: `05_rate_limiter_token_bucket` at `10.60%`
- Highest `net_reduction`: `01_fizzbuzz` at `69.81%`
- Lowest `tool_overhead`: `05_rate_limiter_token_bucket` at `4.65%`
- Highest `tool_overhead`: `04_url_router` at `16.67%`

Source:
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`

## What The Data Proves

1. Diamond syntax compression is large and repeatable on Qwen tokenizer (`~44-56%` in broad runs).
2. Tool-layer overhead is bounded when composition is structural, not additive (`7.80%` final portfolio overhead).
3. Diamond full beats Python with equivalent tooling by a wide margin (`65.29%` reduction).
4. Performance is shape-dependent per program, but portfolio economics are strong under validated gates.

## What The Data Does Not Prove

1. Cross-tokenizer optimality is not yet established as a locked result.
2. Backend parity beyond Python (Rust/Wasm/JS execution) is not yet an economics claim.
3. Worst-shape programs do not guarantee high per-program net compression; they only clear floor gates.

## Reproduce The Numbers

Get tokenizer path:

```bash
TOK="$HOME/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/$(cat ~/.cache/huggingface/hub/models--Qwen--Qwen3-8B/refs/main)/tokenizer.json"
```

Run syntax candidate measurement:

```bash
python3 research/v0/tokenbench/tokenbench.py \
  --cases-dir research/benchmarks/corpus/candidates/C \
  --pattern '*.dm' \
  --tokenizer-json "$TOK" \
  --append-jsonl research/benchmarks/measurements/decision_log.jsonl \
  --run-id run_local_suite_c \
  --question suite5_candidate_check \
  --candidate C
```

Run construct-tool portfolio measurement:

```bash
python research/benchmarks/tools/construct_tool_bench.py \
  --python-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/python \
  --python-tools-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/python_with_tools \
  --diamond-base-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_base \
  --diamond-full-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full \
  --tokenizer-json "$TOK" \
  --run-id run_local_v4_gate_lock \
  --question construct_tool_budget_final \
  --candidate v4_gate_lock \
  --append-jsonl research/benchmarks/measurements/decision_log.jsonl \
  --out-csv research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv
```

## Source Index

- `docs/reference/measurements/observations_q1.md`
- `docs/reference/measurements/amendments_p0_q1.md`
- `docs/reference/measurements/construct_tool_q1_summary.md`
- `docs/reference/measurements/construct_tool_portfolio14_v2_summary.md`
- `docs/reference/measurements/construct_tool_portfolio14_v3_34_summary.md`
- `docs/reference/measurements/construct_tool_portfolio14_v4_math_patch_summary.md`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_validation.md`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`
