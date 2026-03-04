#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate
PYTHONPATH=certification/real-repos/retry/upstream python -m pytest -q certification/real-repos/retry/upstream/retry/tests/test_retry.py
