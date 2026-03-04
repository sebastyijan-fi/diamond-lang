# Token Bench

Purpose: compare Diamond syntax variants by actual tokenizer counts.

## Inputs

- `cases/` contains semantically equivalent programs in different syntax variants.

## Usage

HF tokenizer backend (local path, no download):

```bash
python3 tokenbench.py \
  --cases-dir cases \
  --pattern '*.dm' \
  --hf-tokenizer-path /path/to/local/qwen-tokenizer
```

Direct tokenizer.json backend (recommended for offline deterministic runs):

```bash
python3 tokenbench.py \
  --cases-dir cases \
  --pattern '*.dm' \
  --tokenizer-json /path/to/tokenizer.json
```

External command backend:

```bash
python3 tokenbench.py \
  --cases-dir cases \
  --pattern '*' \
  --tokenizer-cmd 'my_tokenizer_count {file}'
```

The command must print a single integer token count.

Fallback heuristic (not authoritative):

```bash
python3 tokenbench.py --cases-dir cases --pattern '*.dm' --heuristic
```

Append structured JSONL records:

```bash
python3 tokenbench.py \
  --cases-dir ../../benchmarks/corpus/candidates/A \
  --pattern '*.dm' \
  --tokenizer-json /path/to/tokenizer.json \
  --append-jsonl ../../benchmarks/measurements/decision_log.jsonl \
  --run-id run_20260303_a \
  --question 'loops_expression_vs_statement' \
  --candidate A \
  --notes 'first pass'
```
