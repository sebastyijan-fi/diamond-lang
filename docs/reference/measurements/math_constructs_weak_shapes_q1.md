# Math-Construct Hypothesis Check (Q1)

Scope:
- Evaluate whether native math constructs can lift weak/algorithmic shapes.
- Measured with Qwen3-8B tokenizer (`tokenizer.json`) in local environment.
- Baseline scenario for totals: `construct_tool_portfolio14_v3_34_q1.csv`.

## Key Observation

Weak-set composition is mixed:
- Math-heavy: `09_binary_search`
- State/dispatch-heavy: `07_key_value_store_memory`, `11_stack`, `15_event_emitter`

So math constructs can strongly help `09` (and some strong algorithmic programs like `10`), but they do little for three of the four weak programs.

## Micro Pattern Measurements

- Midpoint expression:
  - `(l+r)/2` -> `4` tokens
  - `mid(l,r)` -> `4` tokens
  - `a[(l+r)/2]` -> `7`
  - `a[mid(l,r)]` -> `5`
- Comparison chain:
  - `l<=m&m<=r` -> `6`
  - `l<=m<=r` -> `5`
- Nonnegative delta:
  - `max(0,e.t-s.l)` -> `8`
  - `d0(e.t,s.l)` -> `7`

Interpretation:
- Midpoint helps most when used repeatedly inside index/access contexts.
- `d0` is a small but consistent win for token-bucket math.

## Full Program Variants (Measured)

### 09 Binary Search

Current (`v3.4`):
- base: `85`
- full: `92`

Math-native variants:
- midpoint call form (`m(l,r)`):
  - base: `79` (`-6`)
  - full: `86` (`-6`)
- midpoint infix form (`l$r`) [new operator]:
  - base: `71` (`-14`)
  - full: `78` (`-14`)

### 10 Merge Sort

Current (`v3.4`):
- base: `89`
- full: `97`

Math/split-native variants:
- half split helpers (`l(a)`, `r(a)`):
  - base: `80` (`-9`)
  - full: `89` (`-8`)

### 05 Rate Limiter (current worst net outlier)

Current (`v3.4`):
- full: `150`

Math-native change:
- `max(0,e.t-s.l)` -> `d0(e.t,s.l)`:
  - full: `148` (`-2`)

Note: tool-header inheritance on this file (Proposal 3 generalized) gives a much larger reduction:
- full: `150 -> 135` (`-15`)

## Portfolio Impact Estimate

Baseline totals (`v3.4`):
- `diamond_full_total = 1086`
- `net_reduction = 35.66%`
- `vs_python_with_tools = 62.64%`

If applying math-only best measured edits (`09: -14`, `10: -8`, `05: -2`):
- projected `diamond_full_total = 1062`
- projected `net_reduction ~= 37.09%`

Conclusion:
- Math-native constructs improve algorithmic compression meaningfully.
- Math-only changes are **not sufficient** to reach `40%` portfolio net.
- Biggest remaining low-risk gain is still broad Proposal 3 application (header inheritance everywhere), then Proposal 1 for state-heavy weak programs.

## Recommended Sequence

1. Generalize Proposal 3 to all multi-decl full programs (already validated pattern).
2. Add one native math construct at a time with parser constraints:
   - midpoint operator candidate (`$`) or call-form (`m(l,r)`)
   - half-split intrinsics (`l(a)`, `r(a)`) for divide-and-conquer shapes
   - `d0(a,b)` for nonnegative deltas
3. Re-measure portfolio.
4. Apply Proposal 1 (record patch) for non-math weak shapes (`07/11/15`).
5. Re-check gates.
