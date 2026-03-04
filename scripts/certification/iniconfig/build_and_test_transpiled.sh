#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

. .venv/bin/activate

OUT_BASE="certification/real-repos/iniconfig/out"
TMP_OUT="$OUT_BASE/transpile_tmp"
PKG_OUT="$OUT_BASE/pkg"
DM_IN="certification/real-repos/iniconfig/diamond"
UP_BASE="certification/real-repos/iniconfig/upstream/iniconfig"

rm -rf "$TMP_OUT" "$PKG_OUT"
mkdir -p "$TMP_OUT" "$PKG_OUT/iniconfig" "$PKG_OUT/testing"

if ! ls "$DM_IN"/*.dm >/dev/null 2>&1; then
  echo "[phase-b2] no Diamond source files in $DM_IN"
  echo "[phase-b2] scaffold is ready; add .dm files before running parity."
  exit 2
fi

python src/transpiler/transpile.py \
  --in "$DM_IN" \
  --backend python \
  --out-dir "$TMP_OUT" \
  --dump-ir-json

cp "$TMP_OUT/diamond_runtime.py" "$PKG_OUT/diamond_runtime.py"
cp "$TMP_OUT/parse_dm.py" "$PKG_OUT/iniconfig/parse_dm.py"

cp "$UP_BASE/src/iniconfig/__init__.py" "$PKG_OUT/iniconfig/__init__.py"
cp "$UP_BASE/src/iniconfig/exceptions.py" "$PKG_OUT/iniconfig/exceptions.py"
cp "$UP_BASE/src/iniconfig/py.typed" "$PKG_OUT/iniconfig/py.typed"
cp "$UP_BASE/testing/test_iniconfig.py" "$PKG_OUT/testing/test_iniconfig.py"
cp "$UP_BASE/testing/conftest.py" "$PKG_OUT/testing/conftest.py"

cat > "$PKG_OUT/iniconfig/_parse.py" <<'PY'
from __future__ import annotations

from typing import NamedTuple

import diamond_runtime as dm

from . import parse_dm as _dm
from .exceptions import ParseError

COMMENTCHARS = _dm.commentchars()


class ParsedLine(NamedTuple):
    lineno: int
    section: str | None
    name: str | None
    value: str | None


def _raise_parse_error(exc: dm.IniParseError) -> None:
    raise ParseError(exc.path, exc.lineno, exc.msg) from None


def parse_ini_data(
    path: str,
    data: str,
    *,
    strip_inline_comments: bool,
    strip_section_whitespace: bool = False,
):
    try:
        return _dm.parse_ini_data_dm(
            path,
            data,
            strip_inline_comments,
            strip_section_whitespace,
        )
    except dm.IniParseError as exc:
        _raise_parse_error(exc)


def parse_lines(
    path: str,
    line_iter: list[str],
    *,
    strip_inline_comments: bool = False,
    strip_section_whitespace: bool = False,
) -> list[ParsedLine]:
    try:
        rows = _dm.parse_lines_dm(
            path,
            line_iter,
            strip_inline_comments,
            strip_section_whitespace,
        )
    except dm.IniParseError as exc:
        _raise_parse_error(exc)

    return [ParsedLine(*row) for row in rows]


def _parseline(
    path: str,
    line: str,
    lineno: int,
    strip_inline_comments: bool,
    strip_section_whitespace: bool,
) -> tuple[str | None, str | None]:
    try:
        return _dm.parseline_dm(
            path,
            line,
            lineno,
            strip_inline_comments,
            strip_section_whitespace,
        )
    except dm.IniParseError as exc:
        _raise_parse_error(exc)


def iscommentline(line: str) -> bool:
    return _dm.iscommentline_dm(line)
PY

echo "[phase-b2] full upstream suite"
PYTHONPATH="$PKG_OUT" python -m pytest -q "$PKG_OUT/testing/test_iniconfig.py"
