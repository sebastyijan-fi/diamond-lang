# D10 Module System: B-core vs C-contract (Q1)

Run ids:
- B structure: `run_20260303_d10_b_core_structure_v5`
- C context: `run_20260303_d10_c_contract_context_v5`
- B spec tokens: `run_20260303_d10_b_core_spec`
- C spec tokens: `run_20260303_d10_c_contract_spec_v4`

Tokenizer:
- `Qwen/Qwen3-8B` local `tokenizer.json`

## Spec-budget comparison

| Candidate | spec_tokens (rules payload) | Gate `<=100` |
|---|---:|---|
| B-core | 99 | PASS |
| C-contract | 79 | PASS |

## Structural overhead comparison (same 3 programs)

Both candidates reuse the same full source representation (`*_multiblock.dm` vs `*_singlefile.dm`), so structure metrics are identical:

- `portfolio structure_overhead`: `7.31%`
- `portfolio tokens_per_edge`: `1.58`
- `ambiguity_parse_clean`: `true` (block-body parseability gate)

Per-program structure metrics:

| Program | structure_overhead | tokens_per_edge |
|---|---:|---:|
| `url_parser` | 6.31% | 1.75 |
| `key_value_store` | 7.05% | 1.38 |
| `event_emitter_handlers` | 9.15% | 1.62 |

## C-contract context-pack metrics

`*_context.dm` files model large-codebase generation context: dependency contracts + one active block.

| Program | multiblock_tokens | context_tokens | reduction vs multiblock |
|---|---:|---:|---:|
| `url_parser` | 236 | 120 | 49.15% |
| `key_value_store` | 167 | 135 | 19.16% |
| `event_emitter_handlers` | 155 | 115 | 25.81% |

Portfolio context metrics:
- `multiblock_tokens_total`: `558`
- `context_tokens_total`: `370`
- `contract_tokens_total`: `170`
- `active_body_tokens_total`: `198`
- `context_vs_multiblock_reduction`: `33.69%`

Interpretation:
- B-core remains the default grammar mode.
- C-contract is a viable orchestration extension for context-window pressure: on this set, context packs are ~34% smaller than full multiblock source while keeping parseable active-block bodies.

## Notes

- C-context files compile with generated external stubs for contract-only dependencies; invoking stubbed calls raises explicit runtime `NotImplementedError`.
- Added parser support for line comments (`// ...`) so contract metadata can be parser-ignored without changing core expression semantics.
