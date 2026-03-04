# Profile v1 Validation

Run: `run_20260303_profile_v1_suite10`
Question: `profile_v1_validation_suite10`
Tokenizer: Qwen3-8B `tokenizer.json` (local cache)

## Gate Results

- Unified profile applied across 10 programs: pass
- Ambiguity checks documented: pass
- Grammar authored (EBNF): pass
- Parser check on all 10 profile programs: pass (`10/10`)
- Average token reduction vs Python baseline: pass (`44.26%`)

## Totals

- Profile v1 total: `690` tokens
- Python baseline total: `1238` tokens
- Reduction: `44.26%`

## Per-Program Reduction

- `01_fizzbuzz`: `43` vs `159` (`72.96%`)
- `04_url_router`: `30` vs `75` (`60.00%`)
- `06_http_handler_routing`: `76` vs `128` (`40.62%`)
- `07_key_value_store_memory`: `86` vs `123` (`30.08%`)
- `08_csv_parser`: `21` vs `67` (`68.66%`)
- `09_binary_search`: `92` vs `116` (`20.69%`)
- `10_merge_sort`: `89` vs `175` (`49.14%`)
- `11_stack`: `71` vs `95` (`25.26%`)
- `15_event_emitter`: `77` vs `109` (`29.36%`)
- `16_retry_exponential_backoff`: `105` vs `191` (`45.03%`)

## Artifacts

- Syntax profile: `docs/decisions/profile_v1/SYNTAX_PROFILE.md`
- Ambiguity checks: `docs/decisions/profile_v1/AMBIGUITY_CHECKS.md`
- EBNF: `docs/language/spec/profile_v1.ebnf`
- Parser check script: `docs/language/spec/profile_v1_parser_check.py`
- Profile programs: `docs/decisions/profile_v1/programs/*.dmd`
- Full measurement log: `research/benchmarks/measurements/decision_log.jsonl`
