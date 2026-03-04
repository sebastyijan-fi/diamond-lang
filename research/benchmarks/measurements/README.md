# Measurement Logs

This folder stores structured measurement records for Diamond syntax decisions.

## Files

- `decision_log.jsonl`: append-only run log (create on first real run)
- `decision_log.template.jsonl`: example record shapes
- `ECONOMICS_DEEP_DIVE.md`: source-backed economics overview and reproducibility commands

## Record Types

- `measurement`: one program + one candidate token count
- `summary`: aggregate for a run/candidate batch
- `construct_tool_measurement`: one program with 4-way budget metrics
- `construct_tool_summary`: aggregate 4-way budget metrics

## Usage

Append records from tokenbench:

```bash
python3 research/v0/tokenbench/tokenbench.py \
  --cases-dir research/benchmarks/corpus/candidates/A \
  --pattern '*.dm' \
  --hf-tokenizer-path /path/to/local/qwen-tokenizer \
  --append-jsonl research/benchmarks/measurements/decision_log.jsonl \
  --run-id run_2026_03_03_a \
  --question "loops_expression_vs_statement" \
  --candidate A
```
