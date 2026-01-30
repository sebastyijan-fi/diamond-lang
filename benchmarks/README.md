# Diamond Benchmarks

The `benchmarks/` workspace captures performance, durability, and security measurements for the Diamond (<>) language stack. Its purpose is to ensure that compiler, runtime, tooling, and ecosystem components satisfy quantitative targets as the project evolves.

## Objectives

- **Guard Performance Regressions**: Track compile times, runtime execution latency, continuation resume overhead, and memory usage.
- **Validate Durability Guarantees**: Stress-test algebraic effects, continuation persistence tiers, and resumable workflows.
- **Enforce Security Budgets**: Measure the cost of capability checks, prompt verification, and sandbox isolation.
- **Support Release Readiness**: Provide automated reports that gate release candidates via CI.

## Directory Layout (Planned)

| Path | Description |
|------|-------------|
| `compiler/` | Compile-time microbenchmarks (parser throughput, type-checker latency, Wasm emission cost). |
| `runtime/` | Effect dispatcher, continuation storage, decision engine, and prompt router stress suites. |
| `security/` | Capability enforcement, prompt-injection fuzzing, and Gem registry provenance validation. |
| `tooling/` | Language server responsiveness, transpiler throughput, and formatter performance. |
| `reports/` | Generated benchmark reports (HTML/Markdown/JSON) with trend analysis and regression annotations. |
| `fixtures/` | Shared datasets, synthetic workloads, and serialized continuations used across suites. |

> **Note:** Subdirectories are created alongside their corresponding benchmark suites. Update this README whenever a new suite is added.

## Benchmark Execution Model

1. **Scenario Definitions**  
   Each benchmark scenario is described declaratively (YAML/JSON) to specify inputs, target metrics, acceptable thresholds, and required capabilities.

2. **Harness Implementation**  
   Rust- or shell-based harnesses orchestrate repeats, warm-up runs, and environment setup (e.g., spawning runtimes, seeding continuations, preparing capability manifests).

3. **Result Capture**  
   Metrics are emitted in machine-readable formats (JSON Lines / OpenTelemetry spans) and stored under `reports/` with timestamped filenames.

4. **Regression Detection**  
   CI workflows compare current results against previous baselines. Deviations exceeding configured tolerances fail the pipeline and surface alerts.

## Usage Guidelines

- **Local Runs**  
  ```bash
  ./scripts/dev/bench.sh --suite runtime --report reports/runtime-$(date +%Y%m%d).json
  ```
  The script (planned) ensures repeatable environments, applies dependency checks, and summarizes results.

- **CI Integration**  
  Continuous integration pipelines run targeted suites on nightly and release branches. Thresholds and alerts are configured to match roadmap commitments.

- **Baseline Management**  
  Store baseline results in `reports/` with semantic version tags. When updating thresholds, include justification in `CHANGELOG.md` and link to supporting data.

## Metrics (Illustrative)

| Category | Metric | Target / Threshold |
|----------|--------|--------------------|
| Compiler | Parse throughput (lines/s) | >= 150k lines/s on reference hardware |
| Compiler | Wasm emission time (ms) | <= 500 ms for medium module (5k LOC) |
| Runtime | Continuation resume latency (p95) | <= 20 ms (hot tier), <= 150 ms (warm tier) |
| Runtime | Decision engine accuracy | >= 90% route correctness on benchmark dataset |
| Security | Capability check overhead | <= 5% runtime impact in worst-case scenario |
| Tooling | LSP completion latency (p95) | <= 75 ms for 1k-line file |

## Governance

- Benchmarks are owned collectively by the relevant working groups (Compiler, Runtime, Security, ML Enablement, Developer Experience).
- Updates require review from affected groups and must include rationale, methodology, and hardware/environment specifications.
- Results feed into the roadmap (`docs/spec/roadmap.dm`) for milestone acceptance criteria.

## Future Work

- Add deterministic sandbox environments (container images) for reproducible benchmarking.
- Integrate with OpenTelemetry collector for cross-suite tracing and correlation.
- Publish dashboard visualizations (Grafana/Looker) from `reports/` data streams.
- Create public benchmark profiles to compare different hardware or deployment modes.

---

Keep this README current as the benchmarking infrastructure grows. Accurate documentation ensures every contributor understands how to measure, detect, and prevent regressions in the Diamond ecosystem.