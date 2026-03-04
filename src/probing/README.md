# Automatic Probing Loop

Purpose: continuously probe real repos to discover Diamond core gaps and drive language evolution through measured evidence.

## Single Probe

```bash
. .venv/bin/activate
python src/probing/probe_repo.py \
  --repo-url https://github.com/pallets/click.git \
  --name click_probe \
  --run-tests
```

## Batch Probe

```bash
. .venv/bin/activate
./src/probing/run_probe_batch.sh
```

## Outputs

1. JSON reports:
- `src/probing/reports/run_*_probe_*.json`
2. Measurement log entries:
- `research/benchmarks/measurements/decision_log.jsonl`

Each report includes:
- snapshot commit
- baseline test attempt/result
- AST feature counts
- ranked core-gap signals
- friction score

## Governance

Probe findings are discovery input only. Language promotion still follows:
- `docs/decisions/profile_v1/LANGUAGE_CHANGE_GATE.md`
