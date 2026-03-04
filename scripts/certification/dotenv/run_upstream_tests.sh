#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO="$ROOT/certification/real-repos/dotenv/upstream/python-dotenv"

. "$ROOT/.venv/bin/activate"
PYTHONPATH="$REPO:$REPO/src${PYTHONPATH:+:$PYTHONPATH}" \
  python -m pytest -q "$REPO/tests"
