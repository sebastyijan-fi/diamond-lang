#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate

echo "[1/8] retry baseline"
./scripts/certification/retry/run_upstream_tests.sh

echo "[2/8] iniconfig baseline"
./scripts/certification/iniconfig/run_upstream_tests.sh

echo "[3/8] tomli baseline"
./scripts/certification/tomli/run_upstream_tests.sh

echo "[4/8] retry transpiled parity"
./scripts/certification/retry/build_and_test_transpiled.sh

echo "[5/8] iniconfig transpiled parity"
./scripts/certification/iniconfig/build_and_test_transpiled.sh

echo "[6/8] tomli transpiled parity + differential cases"
./scripts/certification/tomli/run_differential_cases.sh

echo "[7/8] semantic validation on all phase-b Diamond sources"
python src/transpiler/semantic_validate.py \
  --in certification/real-repos/retry/diamond \
  --in certification/real-repos/iniconfig/diamond \
  --in certification/real-repos/tomli/diamond \
  --max-warnings 0

echo "[8/8] capability validation on all phase-b Diamond sources"
python src/transpiler/capability_validate.py \
  --in certification/real-repos/retry/diamond \
  --in certification/real-repos/iniconfig/diamond \
  --in certification/real-repos/tomli/diamond \
  --max-warnings 0

echo "pre-rust certification: PASS"
