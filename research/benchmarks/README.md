# Benchmarks

Starter benchmark set for syntax-compression experiments.

## HTTP Handler Levels

Files:
- `http_handler_levels/level0_python.py`
- `http_handler_levels/level1_terse.dm`
- `http_handler_levels/level2_symbolic.dm`
- `http_handler_levels/level3_alien.dm`

Example run (heuristic tokenizer proxy):

```bash
python3 research/v0/tokenbench/tokenbench.py \
  --cases-dir research/benchmarks/http_handler_levels \
  --pattern '*' \
  --heuristic
```

For real decisions, use a Qwen tokenizer backend (`--hf-tokenizer-path` or `--tokenizer-cmd`).

## Construct-Tool Bench

See `construct_tool/README.md` for the four-way budget model:

- `python`
- `python_with_tools`
- `diamond_base`
- `diamond_full`

Measured with `tools/construct_tool_bench.py`.
