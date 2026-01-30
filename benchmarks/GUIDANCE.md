# Benchmarks Guidance

## Purpose
The `benchmarks/` directory codifies the quantitative validation strategy for Diamond. Every suite, fixture, and report produced here should reinforce the language’s core principles described in `diamond.md`, `diamond2.md`, and `diamond3.md`:

1. **Secure-by-Default Execution** — measure the overhead and robustness of capability enforcement, sandboxing, and decision gating.
2. **Resumable Effects** — track durability characteristics of continuations, effect handlers, and supervisor recovery loops.
3. **Semantic Intent Capture** — evaluate the accuracy of probabilistic routing, prompt verification, and semantic typing at scale.

## Directory Contract
| Path | Contents | Notes |
|------|----------|-------|
| `compiler/` | Parser, type-checker, HIR lowering, and Wasm emission benchmarks. | Include structured scenarios for Golden Path, stress, and adversarial inputs. |
| `runtime/` | Effect dispatcher latency, continuation resume tiers, capability manager throughput, decision engine accuracy. | Instrument for hot/warm/cold tiers and record resumption metadata. |
| `security/` | Capability verification cost, prompt-injection fuzz harnesses, gem registry provenance audits. | Store fuzz seeds & payloads under `fixtures/`. |
| `tooling/` | Language server responsiveness, transpiler throughput, formatter stability. | Maintain cross-version comparisons (nightly vs. release). |
| `fixtures/` | Shared datasets, serialized continuations, synthetic workloads, capability manifests. | Every file must document provenance and usage constraints. |
| `reports/` | Rendered results (JSON, Markdown, HTML), trend analyses, regression annotations. | Use semantic versioned filenames: `vX.Y/runtime-hot.json`. |
| `scripts/` *(planned)* | Executable harnesses (`bench.sh`, `compare.sh`, data upload tools). | Mirror the resumable execution model—save intermediate state. |
| `dashboards/` *(planned)* | Declarative definitions for Grafana/Looker panels. | Source purely from `reports/` artifacts. |

Update this guidance whenever a new suite or reporting channel is introduced so downstream teams understand expectations.

## Benchmark Design Workflow
1. **Define Intent**  
   Draft a scenario spec in `compiler/` (or relevant folder) using YAML/JSON. Capture:
   - Scenario name and purpose.
   - Metrics to record (latency, throughput, accuracy, overhead).
   - Required capabilities (network, filesystem, model access).
   - Acceptable thresholds tied to roadmap milestones (`docs/spec/roadmap.dm`).

2. **Implement Harness**  
   - Prefer Rust for deterministic loops; shell/Python for orchestration.  
   - Harness must emit OpenTelemetry spans or structured JSON lines:
     ```/dev/null/benchmarks_example.jsonl#L1-1
     { "benchmark": "runtime/hot_resume", "p95_ms": 14.2, "capability": "ContinuationStore::Hot" }
     ```
   - Include support for warmups, iterations, and reproducible seeds.

3. **Capture Metadata**  
   - Record environment details: hardware profile, compiler version, runtime build hash.
   - Store continuation snapshots or prompts used in `fixtures/` if reproducibility depends on them.
   - Document any deviations from default capability manifests.

4. **Report & Regressions**  
   - Write summary Markdown with comparison tables under `reports/`.  
   - Attach difference JSON (baseline vs. current).  
   - Flag regressions beyond tolerance and link to tracking issues with labels (`benchmark-regression`, `capability-impact`).

5. **Governance**  
   - Submit changes via PR with reviewers from relevant working groups (Compiler, Runtime, Security, ML Enablement, Developer Experience).  
   - Reference supportive RFCs or spec sections for threshold updates.  
   - Update `CHANGELOG.md` when benchmark targets shift.

## Standard Scenario Archetypes
| Archetype | Description | Example Metrics |
|-----------|-------------|-----------------|
| Golden Path | Steady-state workloads representative of planned production usage. | Parse throughput, effect dispatch latency. |
| Stress | Push limits of continuations, capability gating flows, or prompt routers. | Hot-tier saturation, decision reliability under noise. |
| Adversarial | Simulate prompt injection, capability misuse, malformed modules. | Guardrail success rate, sandbox containment. |
| Regression | Baselines locked to release candidates for comparison. | Delta in p95 vs. previous release. |

Each suite should implement all archetypes where meaningful.

## Resumable Benchmarking Pattern
Benchmarks should mimic Diamond’s effect-resumable runtime:

1. Phase execution steps (`setup`, `warmup`, `measure`, `cooldown`) as discrete continuation checkpoints.
2. Persist checkpoint metadata (e.g., `benchmarks/reports/runtime/hot_resume/meta.json`) to support manual resumption.
3. Provide `scripts/bench_resume.sh` (planned) that can replay from a saved checkpoint—useful for nightly CI that pauses or fails mid-run.

## Security Alignment
- Benchmarks dealing with network or filesystem must rely on explicit capability manifests stored in `fixtures/capabilities/`.
- Fuzzing campaigns require review by Security WG and should log every mutated payload plus sanitization status to `reports/security/fuzz-<timestamp>.json`.
- Never store secrets; use synthetic credentials with documented scope.

## Tooling & Automation Hooks
- CI (`.github/workflows/nightly.yml`, planned) triggers nightly runs for selected suites; results uploaded as artifacts tagged with suite and timestamp.
- Future automation should:
  - Post regression summaries to the observability channel (`scripts/ci/post_failure_summary.py`, planned).
  - Update dashboards automatically if new report formats appear.

## Documentation Expectations
Every suite directory must ship a `README.md` detailing:
- Scope and intent.
- Scenario definitions and thresholds.
- Reproduction steps.
- Data provenance and licensing.
This guidance file serves as the authoritative checklist; keep suite READMEs consistent with updates here.

## Open Tasks
- [ ] Scaffold scenario schema (`benchmarks/schema/benchmark.schema.json`).
- [ ] Implement `scripts/dev/bench.sh` with resumable execution.
- [ ] Design initial dashboards for compiler/runtime latency.
- [ ] Define baseline thresholds derived from `docs/spec/roadmap.dm` acceptance criteria.
- [ ] Add OCap audit hooks to ensure benchmark harnesses declare capabilities.

Maintaining disciplined benchmarks ensures Diamond remains performant, durable, and secure as the language matures. Align every new measurement with the specification trilogy to keep the project’s intent crystalline.