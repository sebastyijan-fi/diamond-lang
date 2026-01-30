# Diamond Bootstrapping Strategy

This document describes the end-to-end plan for creating the foundational data, tooling, and model support required to make Diamond (<>) viable.

## Objectives
- Generate a high-fidelity Diamond code corpus suitable for continued pre-training (CPT) and fine-tuning.
- Deliver tooling that converts existing ecosystems into idiomatic Diamond while preserving security guarantees.
- Establish evaluation harnesses that measure compilation success, semantic correctness, and capability compliance.
- Validate that trained models can author production-grade Diamond code across representative agent scenarios.

## Guiding Principles
- **Fidelity over volume**: accept smaller datasets if they maximize semantic accuracy and security conformance.
- **Automation with verification**: every automated step is paired with linting, compilation, and security checks.
- **LLM-first ergonomics**: data and tooling mirror the language constructs and patterns LLMs must internalize.
- **Continuous evaluation**: nightly signals drive pipeline iterations; regressions block downstream releases.

## Program Phases

1. **Specification Freeze Alignment**
   - Finalize grammar, type system, effects, capability model, and standard library MVP.
   - Publish machine-readable spec artifacts (EBNF, JSON schemas, WIT signatures).
   - Produce seed examples curated for canonical agent workflows.

2. **Python → Diamond Transpilation Pipeline**
   - Define the supported Python subset (type-hinted, side-effect boundaries, async patterns).
   - Implement a structural transpiler that maps Python AST nodes to Diamond constructs.
   - Enforce capability manifests during translation to avoid reintroducing ambient authority.
   - Generate paired unit tests to ensure semantic equivalence for each translated module.

3. **LLM-Guided Code Evolution**
   - Use high-quality models with the locked spec to rewrite transpiled code into idiomatic Diamond.
   - Apply automatic critique loops (self-review, style enforcement, effect annotation checks).
   - Persist lineage metadata: `source_python -> transpiled_dm -> evolved_dm`.
   - Require compilation success and lint pass before accepting evolved outputs.

4. **Semantic Augmentation & Documentation**
   - Autogenerate docstrings, comments, and developer notes describing intent and capability usage.
   - Produce natural-language problem statements for supervised fine-tuning.
   - Attach semantic refinement annotations (regex, verifier prompts) wherever applicable.

5. **Corpus Validation & Packaging**
   - Compile the entire corpus nightly with the reference compiler.
   - Execute unit/integration tests using the runtime harness in deterministic mode.
   - Run security scanners for capability leaks, forbidden imports, and prompt-injection vectors.
   - Version and shard the corpus into training-ready bundles (by domain, effect usage, capability profile).

6. **Model Enablement & Evaluation**
   - Perform continued pre-training (CPT) on a base model using the curated corpus.
   - Fine-tune instruction-following checkpoints for Diamond authoring tasks.
   - Evaluate via compilation rate, semantic correctness, and agent scenario benchmarks.
   - Iterate on data quality based on evaluation deltas.

## Data Generation Pipelines

| Pipeline | Input | Output | Quality Gates |
|----------|-------|--------|---------------|
| Transpiler | Typed Python AST | Draft Diamond code | AST parity tests, capability lint |
| Evolution | Draft Diamond code | Idiomatic Diamond code | Compiler pass, style lint, effect coverage |
| Augmentation | Idiomatic Diamond | Narrative docs, tests, prompts | Doc completeness, test coverage thresholds |
| Synthetic Tasks | Spec primitives | Focused micro-programs | Human spot-check, semantic validator |

## Tooling Stack
- **Transpiler CLI**: Converts Python packages and emits alignment metadata.
- **Diamond LSP**: Provides diagnostics during evolution loops, ensuring generated code respects the spec.
- **Corpus Orchestrator**: Schedules pipeline stages, tracks lineage, and reports metrics.
- **Verifier Suite**: Runs regex/grammar checkers, semantic classifier models, and capability analyzers.
- **Benchmark Harness**: Executes canonical agent tasks against runtime builds.

## Quality Metrics
- **Compilation Success Rate**: Target ≥ 95% per nightly build.
- **Semantic Drift**: ≤ 2% discrepancy between Python source tests and Diamond equivalents.
- **Capability Compliance**: 0 critical violations; warn on attenuable leaks.
- **Prompt Validity**: ≥ 99% passes through constrained-decoding validators.
- **Model Performance**: Instruction-tuned checkpoint achieves ≥ 80% compile rate and ≥ 60% task success on curated benchmark.

## Evaluation Framework
- Maintain a dedicated `benchmarks/bootstrapping` suite with scenario-driven tests.
- Run A/B comparisons between corpus versions to quantify improvement or regressions.
- Use telemetry dashboards to visualize compiler errors, effect usage, capability leaks.
- Engage human reviewers for weekly spot checks on randomly sampled outputs.

## Risks & Mitigations
- **Spec Drift**: Mitigate via versioned spec artifacts and compatibility tests.
- **Low-Quality Transpilation**: Maintain allowlists/denylists for libraries; prioritize curated datasets.
- **Model Overfitting**: Mix synthetic and handwritten examples; introduce noise-resistant evaluation tasks.
- **Security Regression**: Integrate capability fuzzing and prompt-injection adversarial tests in CI.
- **Pipeline Latency**: Use incremental builds, caching, and distributed workers.

## Milestone Timeline (Indicative)
- **M1 (Month 0-2)**: Spec artifacts frozen, transpiler prototype compiling 10k functions.
- **M2 (Month 3-5)**: Evolution loop automated, nightly corpus of 50M tokens with ≥ 90% compile rate.
- **M3 (Month 6-8)**: Semantic augmentation complete, CPT model checkpoints available.
- **M4 (Month 9-12)**: Fine-tuned models hit target benchmarks; corpus published for community evaluation.

## Ownership & Governance
- **Bootstrapping WG Lead**: Coordinates cross-functional efforts and roadmap.
- **Spec Team**: Reviews language changes impacting data generation.
- **Compiler Team**: Maintains transpiler, evolution lint rules, and validation harness.
- **ML Enablement**: Drives CPT/fine-tune cycles, evaluation design, model release notes.
- **Security Team**: Audits capability manifests, oversees red-team exercises.

## References
- `docs/spec/overview.md` — canonical language summary.
- `docs/spec/grammar.md` — EBNF grammar used by transpiler front-end.
- `docs/spec/types.md` — structural and semantic typing rules.
- `docs/spec/effects.md` — algebraic effects semantics for evolution linting.
- `docs/spec/capabilities.md` — capability enforcement baseline.
- `docs/spec/runtime.md` — runtime integration points for benchmarking.

## Change Log
- **v0.1** — Initial synthesis of bootstrapping strategy (this document).