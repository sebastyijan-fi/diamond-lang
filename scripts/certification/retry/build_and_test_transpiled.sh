#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate

OUT_BASE="certification/real-repos/retry/out"
TMP_OUT="$OUT_BASE/transpile_tmp"
PKG_OUT="$OUT_BASE/pkg"

rm -rf "$TMP_OUT" "$PKG_OUT"
mkdir -p "$TMP_OUT" "$PKG_OUT/retry/tests"

python src/transpiler/transpile.py \
  --in certification/real-repos/retry/diamond \
  --backend python \
  --out-dir "$TMP_OUT" \
  --dump-ir-json

cp "$TMP_OUT/diamond_runtime.py" "$PKG_OUT/diamond_runtime.py"
cp "$TMP_OUT/api_dm.py" "$PKG_OUT/retry/api_dm.py"
cp certification/real-repos/retry/upstream/retry/__init__.py "$PKG_OUT/retry/__init__.py"
cp certification/real-repos/retry/upstream/retry/compat.py "$PKG_OUT/retry/compat.py"
cp certification/real-repos/retry/upstream/retry/tests/__init__.py "$PKG_OUT/retry/tests/__init__.py"
cp certification/real-repos/retry/upstream/retry/tests/test_retry.py "$PKG_OUT/retry/tests/test_retry.py"

cat > "$PKG_OUT/retry/api.py" <<'PY'
import logging

from . import api_dm as _dm_api

logging_logger = logging.getLogger(__name__)


def __retry_internal(
    f,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    logger=logging_logger,
):
    return _dm_api.retry_call_core(f, None, None, exceptions, tries, delay, max_delay, backoff, jitter, logger)


def retry(
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    logger=logging_logger,
):
    return _dm_api.retry_core(exceptions, tries, delay, max_delay, backoff, jitter, logger)


def retry_call(
    f,
    fargs=None,
    fkwargs=None,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    logger=logging_logger,
):
    return _dm_api.retry_call_core(f, fargs, fkwargs, exceptions, tries, delay, max_delay, backoff, jitter, logger)
PY

echo "[phase-b] retry_call-only subset"
PYTHONPATH="$PKG_OUT" python -m pytest -q "$PKG_OUT/retry/tests/test_retry.py" -k "retry_call"

echo "[phase-b] full upstream suite"
PYTHONPATH="$PKG_OUT" python -m pytest -q "$PKG_OUT/retry/tests/test_retry.py"
