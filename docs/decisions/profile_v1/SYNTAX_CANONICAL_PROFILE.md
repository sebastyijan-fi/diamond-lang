# Diamond V1 Canonical Syntax Profile (Measured)

This profile records syntax forms selected by token-cost evidence, not preference.

## Tokenizer baseline

- Tokenizer: `Qwen/Qwen3-8B`
- Evidence artifacts:
- `research/benchmarks/measurements/syntax_minimization/object_surface_results.csv`
- `research/benchmarks/measurements/syntax_minimization/receiver_surface_sweep_qwen3.csv`

## Canonical selections

- Class sigil: `$`
- Receiver binder: `#`
- Receiver declaration in methods: implicit (no explicit `self` parameter)

## Notes

- Receiver sweep showed implicit receiver forms beat explicit receiver declarations in tested contexts.
- `#` and `$`-receiver tied in token cost on tested snippets; `#` is selected to avoid conflict with class sigil `$`.
- Any future syntax candidate must be accepted via evidence gate before profile changes.

## Change policy

- Update this profile only with attached measurement artifacts and conformance pass.
- If a candidate is lower-token but harms semantic determinism, reject it.
- CI enforcement entrypoint: `scripts/canonical/validate_canonical_syntax.py`.
- Experimental syntax can be tested by setting `DIAMOND_EXPERIMENTAL_SYNTAX=1` (violations downgraded to warnings).
