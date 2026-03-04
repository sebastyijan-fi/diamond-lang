# Diamond Design Evidence Gate

Purpose: enforce measurable language improvements instead of unverified syntax changes.

## Rule

A language/syntax change is acceptable only when:

- semantic behavior remains conformant,
- token-cost evidence is statistically favorable,
- confidence bounds do not include negative improvement.

## Evidence command

Use `research/benchmarks/tools/syntax_evidence_gate.py` on CSV outputs from `construct_tool_bench.py`.

Example:

```bash
python3 research/benchmarks/tools/syntax_evidence_gate.py \
  --baseline-csv /tmp/diamond_baseline_run1.csv \
  --baseline-csv /tmp/diamond_baseline_run2.csv \
  --candidate-csv /tmp/diamond_candidate_run1.csv \
  --candidate-csv /tmp/diamond_candidate_run2.csv \
  --metric net_reduction \
  --bootstrap-samples 5000 \
  --min-mean-improvement 0.005 \
  --min-ci-lower 0.0 \
  --min-prob-positive 0.90 \
  --out-json /tmp/diamond_syntax_evidence.json \
  --out-md docs/completeness/SYNTAX_EVIDENCE_REPORT.md
```

## Metrics orientation

- Positive-is-better metrics:
- `syntax_reduction`
- `net_reduction`
- `vs_python_with_tools`
- Lower-is-better metric:
- `tool_overhead` (improvement is computed as `baseline - candidate`).

## Interpretation

- `mean improvement`: expected directional gain.
- `ci95 lower bound`: robustness of gain under resampling.
- `p(improvement > 0)`: probability candidate beats baseline on oriented metric.

## Default thresholds

- `min_mean_improvement = 0.005` (0.5 percentage points)
- `min_ci_lower = 0.0`
- `min_prob_positive = 0.90`

Adjust thresholds per experiment, but do not relax without explicit decision log entry.
