#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate
PYTHONPATH=certification/real-repos/iniconfig/upstream/iniconfig/src \
  python -m pytest -q certification/real-repos/iniconfig/upstream/iniconfig/testing/test_iniconfig.py
