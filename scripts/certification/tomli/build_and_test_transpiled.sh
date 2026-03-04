#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate

OUT_BASE="certification/real-repos/tomli/out"
TMP_OUT="$OUT_BASE/transpile_tmp"
PKG_OUT="$OUT_BASE/pkg"
DM_IN="certification/real-repos/tomli/diamond"
UP_BASE="certification/real-repos/tomli/upstream/tomli"

rm -rf "$TMP_OUT" "$PKG_OUT"
mkdir -p "$TMP_OUT" "$PKG_OUT/tomli" "$PKG_OUT/tests"

python src/transpiler/transpile.py \
  --in "$DM_IN" \
  --backend python \
  --out-dir "$TMP_OUT" \
  --dump-ir-json

cp "$TMP_OUT/diamond_runtime.py" "$PKG_OUT/diamond_runtime.py"
cp "$TMP_OUT/re_tz.py" "$PKG_OUT/tomli/re_tz_dm.py"
cp "$TMP_OUT/re_number.py" "$PKG_OUT/tomli/re_number_dm.py"
cp "$TMP_OUT/re_match.py" "$PKG_OUT/tomli/re_match_dm.py"

cp "$UP_BASE/src/tomli/__init__.py" "$PKG_OUT/tomli/__init__.py"
cp "$UP_BASE/src/tomli/_parser.py" "$PKG_OUT/tomli/_parser.py"
cp "$UP_BASE/src/tomli/_types.py" "$PKG_OUT/tomli/_types.py"
cp "$UP_BASE/src/tomli/py.typed" "$PKG_OUT/tomli/py.typed"

cp "$UP_BASE/tests/__init__.py" "$PKG_OUT/tests/__init__.py"
cp "$UP_BASE/tests/burntsushi.py" "$PKG_OUT/tests/burntsushi.py"
cp "$UP_BASE/tests/test_data.py" "$PKG_OUT/tests/test_data.py"
cp "$UP_BASE/tests/test_error.py" "$PKG_OUT/tests/test_error.py"
cp "$UP_BASE/tests/test_misc.py" "$PKG_OUT/tests/test_misc.py"
mkdir -p "$PKG_OUT/tests/data"
cp -r "$UP_BASE/tests/data/"* "$PKG_OUT/tests/data/"

cat > "$PKG_OUT/tomli/_re.py" <<'PY'
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

from __future__ import annotations

from functools import lru_cache
import re

from . import re_match_dm as _match_dm
from . import re_number_dm as _number_dm
from . import re_tz_dm as _tz_dm

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any, Final

    from ._types import ParseFloat

_TIME_RE_STR: Final = r"""
([01][0-9]|2[0-3])             # hours
:([0-5][0-9])                  # minutes
(?:
    :([0-5][0-9])              # optional seconds
    (?:\.([0-9]{1,6})[0-9]*)?  # optional fractions of a second
)?
"""

RE_NUMBER: Final = re.compile(
    r"""
0
(?:
    x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*   # hex
    |
    b[01](?:_?[01])*                 # bin
    |
    o[0-7](?:_?[0-7])*               # oct
)
|
[+-]?(?:0|[1-9](?:[0-9])*)         # dec, integer part
(?P<floatpart>
    (?:\.[0-9](?:[0-9])*)?         # optional fractional part
    (?:[eE][+-]?[0-9](?:[0-9])*)?  # optional exponent part
)
""",
    flags=re.VERBOSE,
)
RE_LOCALTIME: Final = re.compile(_TIME_RE_STR, flags=re.VERBOSE)
RE_DATETIME: Final = re.compile(
    rf"""
([0-9]{{4}})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])  # date, e.g. 1988-10-27
(?:
    [Tt ]
    {_TIME_RE_STR}
    (?:([Zz])|([+-])([01][0-9]|2[0-3]):([0-5][0-9]))?  # optional time offset
)?
""",
    flags=re.VERBOSE,
)


# Wire cross-file Diamond dependencies.
_match_dm.tzo = _tz_dm.tzo


def match_to_datetime(match: re.Match[str]):
    return _match_dm.mtd(match)


@lru_cache(maxsize=None)
def cached_tz(hour_str: str, minute_str: str, sign_str: str):
    return _tz_dm.tzo(hour_str, minute_str, sign_str)


def match_to_localtime(match: re.Match[str]):
    return _match_dm.mtl(match)


def match_to_number(match: re.Match[str], parse_float: ParseFloat):
    return _number_dm.mtn(match, parse_float)
PY

echo "[phase-b3] full upstream suite"
PYTHONPATH="$PKG_OUT" python -m pytest -q "$PKG_OUT/tests"
