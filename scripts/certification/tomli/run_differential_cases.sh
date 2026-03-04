#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate

# Ensure transpiled package is fresh before diffing.
./scripts/certification/tomli/build_and_test_transpiled.sh

python scripts/certification/tomli/diff_all_cases.py
