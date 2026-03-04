# Reference Map

This file keeps long-tail docs discoverable without forcing everyone to read them.

Language design and policy:
- `language/LANGUAGE_DESIGN.md`
- `language/LANGUAGE_DESIGN_AMENDMENTS.md`
- `language/LANGUAGE_CONSTRUCT_TOOL_FRAMEWORK.md`
- `decisions/profile_v1/`
- `decisions/profile_v1/SEMANTIC_CONTRACTS.md`
- `decisions/profile_v1/OBJECT_SEMANTICS_V1.md`
- `decisions/profile_v1/SAFETY_POLICY_V1.md`
- `decisions/profile_v1/CAPABILITY_MODEL_V1.md`
- `decisions/profile_v1/MODULE_DEPENDENCY_POLICY_V1.md`
- `decisions/profile_v1/EVOLUTION_POLICY_V1.md`
- `decisions/profile_v1/INTEROP_POLICY_V1.md`
- `decisions/profile_v1/EQUALITY_IDENTITY_HASH_POLICY_V1.md`
- `decisions/profile_v1/PANIC_CLEANUP_POLICY_V1.md`
- `decisions/profile_v1/CONCURRENCY_POLICY_V1.md`
- `decisions/profile_v1/MEMORY_RUNTIME_POLICY_V1.md`

Specs and parser checks:
- `language/spec/` (EBNF and parser checks)

Implementation details:
- `../src/transpiler/ARCHITECTURE_DEEP_DIVE.md`
- `../src/transpiler/README.md`
- `../src/conformance/README.md`
- `../src/probing/README.md`

Measurements and economics:
- `../research/benchmarks/measurements/`
- `../research/benchmarks/construct_tool/`
- `../research/benchmarks/tools/`
- `./reference/measurements/` (historical/intermediate)

Certification and real repos:
- `../certification/real-repos/` (compatibility entrypoints + evidence records)
- `./reference/certification/` (historical/intermediate)

Historical material:
- `../research/v0/`

## Repository confidence layers

- Canonical implementation and validation guidance: `src/`, `scripts/`, `docs/decisions/`
- Compatibility evidence and historical artifacts: `certification/real-repos`, `docs/reference/`
