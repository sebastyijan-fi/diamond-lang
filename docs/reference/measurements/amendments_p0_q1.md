# P0 Amendment Results (Q1)

Date: 2026-03-03
Tokenizer: Qwen/Qwen3-8B (`tokenizer.json`)

## P0-1 Whitespace Hypothesis Test

Question:
- Is C-formatted (indented/newline style) cheaper than C-dense?

Run:
- `run_20260303_whitespace_p0`
- Question key: `whitespace_dense_vs_formatted_c`
- Programs: `01, 06, 07, 10, 16`

Result:
- Dense total: `341`
- Formatted total: `529`
- Dense advantage: `188` tokens (`35.54%` fewer than formatted)

Conclusion:
- For this tokenizer and these winning C programs, dense formatting is materially better.
- Whitespace elimination remains a valid optimization direction.

## P0-2 Keyword Cost Verification

Question:
- Are symbols always cheaper than keyword-like spellings?

Artifacts:
- Candidate sets: `research/benchmarks/hypotheses/keywords/candidates_q1.json`
- Context templates: `research/benchmarks/hypotheses/keywords/contexts_q1.json`
- Raw results JSON: `research/benchmarks/measurements/keyword_cost_q1.json`
- Raw results CSV: `research/benchmarks/measurements/keyword_cost_q1.csv`
- Generated profile: `research/profiles/qwen3-8b.q1.surface.json`

Findings:
- Raw per-operator minima strongly favored symbols/punctuation in this candidate set.
- Independent minima collide across operators (`!` wins multiple operators), so uniqueness constraints are mandatory.
- A distinct mapping was generated via greedy unique assignment (`mappings_unique` in profile JSON).

Conclusion:
- Keyword-vs-symbol must be evaluated with both token cost and global distinctness.
- Punctuation-heavy spellings can be cheapest on Qwen, but ambiguity/disambiguation constraints remain the gating factor.

## Immediate Impact On Freeze Criteria

Before syntax freeze:
1. Keep dense style as default emitter strategy for Qwen profile.
2. Require distinct-operator assignment when generating surface profiles.
3. Add parser ambiguity checks for any punctuation-heavy winner set before adoption.
