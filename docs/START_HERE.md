# Start Here

This repo has many deep-dive documents. Read this path in order:

1. [`STATUS.md`](./STATUS.md) (current status and what is working)
2. [`completeness/STATUS_REPORT.md`](./completeness/STATUS_REPORT.md) (implemented vs excluded inventory)
3. [`decisions/profile_v1/SEMANTIC_CONTRACTS.md`](./decisions/profile_v1/SEMANTIC_CONTRACTS.md) (normative behavior surface)
4. [`../src/transpiler/README.md`](../src/transpiler/README.md) (implementation structure)
5. [`../scripts/ci/README.md`](../scripts/ci/README.md) (quality-gate execution)

Normative profile contracts (do not infer from historical docs over these):
- `decisions/profile_v1/OBJECT_SEMANTICS_V1.md`
- `decisions/profile_v1/SAFETY_POLICY_V1.md`
- `decisions/profile_v1/CAPABILITY_MODEL_V1.md`
- `decisions/profile_v1/MODULE_DEPENDENCY_POLICY_V1.md`
- `decisions/profile_v1/EVOLUTION_POLICY_V1.md`
- [`decisions/profile_v1/INTEROP_POLICY_V1.md`](./decisions/profile_v1/INTEROP_POLICY_V1.md)
- [`decisions/profile_v1/EQUALITY_IDENTITY_HASH_POLICY_V1.md`](./decisions/profile_v1/EQUALITY_IDENTITY_HASH_POLICY_V1.md)
- [`decisions/profile_v1/PANIC_CLEANUP_POLICY_V1.md`](./decisions/profile_v1/PANIC_CLEANUP_POLICY_V1.md)
- [`decisions/profile_v1/CONCURRENCY_POLICY_V1.md`](./decisions/profile_v1/CONCURRENCY_POLICY_V1.md)
- [`decisions/profile_v1/MEMORY_RUNTIME_POLICY_V1.md`](./decisions/profile_v1/MEMORY_RUNTIME_POLICY_V1.md)

If you need details after that:
- Language and decision reference: [`decisions/profile_v1/`](./decisions/profile_v1/)
- Grammar/spec details: [`language/spec/`](./language/spec/)
- Token-economics evidence: [`../research/benchmarks/`](../research/benchmarks/)
- Real-repo parity evidence: [`../certification/real-repos/`](../certification/real-repos/)
