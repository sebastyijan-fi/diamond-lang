# Construct-Tool Bench

This workspace measures the four-way model from `docs/language/LANGUAGE_CONSTRUCT_TOOL_FRAMEWORK.md`.

## Inputs

Program stems must match across all four directories:

- `python/`                 baseline Python (no tooling)
- `python_with_tools/`      Python with equivalent tooling added manually
- `diamond_base/`           Diamond syntax only (tool layer disabled)
- `diamond_full/`           Diamond with construct tool layer enabled

Example matching stems:

- `01_fizzbuzz.py` in `python/` and `python_with_tools/`
- `01_fizzbuzz.dm` in `diamond_base/` and `diamond_full/`

## Metrics

For each program and totals:

- `syntax_reduction = (python - diamond_base) / python`
- `tool_overhead = (diamond_full - diamond_base) / diamond_base`
- `net_reduction = (python - diamond_full) / python`
- `vs_python_with_tools = (python_with_tools - diamond_full) / python_with_tools`

## Run

```bash
. .venv/bin/activate
TOK="$HOME/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/$(cat ~/.cache/huggingface/hub/models--Qwen--Qwen3-8B/refs/main)/tokenizer.json"

python research/benchmarks/tools/construct_tool_bench.py \
  --python-dir research/benchmarks/construct_tool/python \
  --python-tools-dir research/benchmarks/construct_tool/python_with_tools \
  --diamond-base-dir research/benchmarks/construct_tool/diamond_base \
  --diamond-full-dir research/benchmarks/construct_tool/diamond_full \
  --tokenizer-json "$TOK" \
  --run-id run_YYYYMMDD_construct_tool_q1 \
  --question construct_tool_budget \
  --candidate profile_v1 \
  --append-jsonl research/benchmarks/measurements/decision_log.jsonl \
  --out-csv research/benchmarks/measurements/construct_tool_q1.csv
```
