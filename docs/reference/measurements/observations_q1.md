# Diamond Token Observations (Qwen Q3-8B, Q1)

Tokenizer backend:
- Qwen `tokenizer.json` from local HF cache
- path recorded in `decision_log.jsonl`

Runs used:
- `run_20260303_http_levels_qwen3_8b`
- `run_20260303_fizzbuzz_q1`
- `run_20260303_hypotheses_q1`
- `run_20260303_suite5_q1`

## 1) Winner Analysis

### HTTP compression spectrum

- Python: `115`
- Terse human: `84`
- Symbolic structured: `76`
- Alien inline: `54`

Reduction of alien vs Python: `53.04%`.

### FizzBuzz A/B/C + Python

- Python baseline: `159`
- A: `94`
- B: `82`
- C: `48`

Reduction of C vs Python: `69.81%`.

## 2) What likely drove C/alien wins

Observed in token traces:

- No whitespace/newline overhead in winners.
- Very short identifiers (`f`, `z`, `i`, `m`, `p`) reduce repeated identifier tokens.
- Dense inline branching (`?:`) avoids repeated block scaffolding (`if`, braces, `else`).
- Type/shape compression (`I`, `S`, `>[S]`, `!S`) reduces keyword overhead.
- Some symbol sequences appear efficiently chunked by Qwen tokenizer (for example `:[`, `]=`, `?"`, `":`).

Caveat:
- Not every symbol pattern is cheap. Some split into single-character tokens.
- The win is from specific compact patterns, not symbols alone.

## 3) Isolated Hypothesis Tests

From `run_20260303_hypotheses_q1`:

- names_long_vs_short: `44 -> 32` (`27.27%` reduction)
- branch_blocks_vs_inline: `51 -> 32` (`37.25%` reduction)
- keywords_words_vs_symbols: `24 -> 20` (`16.67%` reduction)
- whitespace_spaced_vs_dense: `35 -> 24` (`31.43%` reduction)
- result_wordy_vs_compact: `31 -> 19` (`38.71%` reduction)

Interpretation:
- Largest effects came from branch form, result/type form, and density.
- Keyword/symbol swap alone helps, but less than structural compression.

## 4) Generalization Across Program Shapes (5-program suite)

Programs: `01, 06, 07, 10, 16`.

Totals:
- Python baseline: `776`
- A: `516` (`33.51%` reduction)
- B: `471` (`39.30%` reduction)
- C: `341` (`56.06%` reduction)

Per-program winner among A/B/C:
- `01_fizzbuzz`: C (`48`)
- `06_http_handler_routing`: C (`77`)
- `07_key_value_store_memory`: C (`59`)
- `10_merge_sort`: C (`93`)
- `16_retry_exponential_backoff`: C (`64`)

Result:
- C won all 5 tested program shapes.

## 5) Provisional Design Principles (measured, not aesthetic)

1. Prefer expression-dense control flow over block-heavy scaffolding when parseability is preserved.
2. Minimize repeated identifier length; single-character scope-local naming is consistently cheaper.
3. Use compact type/result encodings; long type words are expensive.
4. Remove optional whitespace/newlines in generated form.
5. Keep a whitelist of proven-cheap token patterns; do not assume arbitrary symbol clusters are efficient.

## 6) Next Measurement Priorities

- Validate on another 5 programs (for 10 total) before freezing any construct.
- Add ambiguity scoring pass so token wins do not hide parse ambiguity.
- Break out construct-level benchmarks (loops, pattern match, map/dict literals, function signatures) with paired micro tests.
