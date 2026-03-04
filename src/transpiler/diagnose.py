#!/usr/bin/env python3
"""Diamond parser diagnostics with machine-readable JSON output."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark.exceptions import UnexpectedCharacters, UnexpectedInput

from parse_to_ir import build_parser, iter_inputs, parse_source


SCHEMA_VERSION = "dm_diagnose_v0"


@dataclass
class Diagnostic:
    code: str
    stage: str
    message: str
    span_start: int | None
    span_end: int | None
    line: int | None
    col: int | None
    got_token: str | None
    expected_tokens: list[str]
    hint: str


@dataclass
class FileDiagnostics:
    file: str
    ok: bool
    diagnostics: list[Diagnostic]


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hint(got_token: str | None, expected_tokens: list[str]) -> str:
    exp = set(expected_tokens)
    if got_token == "$END":
        return "Add a missing expression or closing delimiter before end of input."
    if got_token and len(got_token) == 1 and not got_token.isalnum():
        return "Replace or remove unexpected punctuation at the error span."
    if {"IDENT", "NUMBER", "STRING", "TRUE", "FALSE"} & exp:
        return "Insert a valid expression token (identifier, literal, or grouped expression)."
    if {"RPAR", "RBRACE", "RSQB"} & exp:
        return "Check delimiter balance near this location."
    return "Replace token at span with one of expected_tokens."


def _diag_from_unexpected(exc: UnexpectedInput) -> Diagnostic:
    if isinstance(exc, UnexpectedCharacters):
        pos = getattr(exc, "pos_in_stream", None)
        got = getattr(exc, "char", None)
        expected = sorted(getattr(exc, "allowed", set()) or [])
        return Diagnostic(
            code="DM_PARSE_UNEXPECTED_CHAR",
            stage="parse",
            message=f"Unexpected character {got!r}.",
            span_start=pos,
            span_end=(None if pos is None else pos + 1),
            line=getattr(exc, "line", None),
            col=getattr(exc, "column", None),
            got_token=got,
            expected_tokens=expected,
            hint=_hint(got, expected),
        )

    token = getattr(exc, "token", None)
    got_token: str | None = None
    span_start: int | None = getattr(exc, "pos_in_stream", None)
    span_end: int | None = None
    if token is not None:
        got_token = getattr(token, "type", None) or None
        start = getattr(token, "start_pos", None)
        end = getattr(token, "end_pos", None)
        if start is not None:
            span_start = start
        if end is not None:
            span_end = end
    if span_end is None and span_start is not None:
        span_end = span_start if got_token == "$END" else span_start + 1

    expected = sorted(getattr(exc, "expected", set()) or [])
    got_display = got_token or "UNKNOWN"
    exp_preview = ", ".join(expected[:8]) if expected else "none"
    message = f"Unexpected token {got_display}; expected one of: {exp_preview}."
    return Diagnostic(
        code="DM_PARSE_UNEXPECTED_TOKEN",
        stage="parse",
        message=message,
        span_start=span_start,
        span_end=span_end,
        line=getattr(exc, "line", None),
        col=getattr(exc, "column", None),
        got_token=got_token,
        expected_tokens=expected,
        hint=_hint(got_token, expected),
    )


def diagnose_source(source: str, module_name: str, parser: Any) -> list[Diagnostic]:
    try:
        parse_source(source, module_name=module_name, parser=parser)
        return []
    except UnexpectedInput as exc:
        return [_diag_from_unexpected(exc)]
    except Exception as exc:  # noqa: BLE001
        return [
            Diagnostic(
                code="DM_IR_BUILD_ERROR",
                stage="ir_build",
                message=str(exc),
                span_start=None,
                span_end=None,
                line=None,
                col=None,
                got_token=None,
                expected_tokens=[],
                hint="Parser built a tree but IR construction failed; inspect declaration structure near reported message.",
            )
        ]


def diagnose_file(path: Path, parser: Any) -> FileDiagnostics:
    source = path.read_text(encoding="utf-8")
    diags = diagnose_source(source, module_name=path.name, parser=parser)
    return FileDiagnostics(file=str(path), ok=(len(diags) == 0), diagnostics=diags)


def run(in_path: Path) -> dict[str, Any]:
    parser = build_parser()
    files = iter_inputs(in_path)
    if not files:
        return {
            "schema_version": SCHEMA_VERSION,
            "ts_utc": _now_utc(),
            "input": str(in_path),
            "ok": False,
            "error_count": 0,
            "file_count": 0,
            "files": [],
            "message": "no input .dmd files found",
        }

    results = [diagnose_file(path, parser=parser) for path in files]
    error_count = sum(len(r.diagnostics) for r in results)
    ok = error_count == 0
    return {
        "schema_version": SCHEMA_VERSION,
        "ts_utc": _now_utc(),
        "input": str(in_path),
        "ok": ok,
        "error_count": error_count,
        "file_count": len(results),
        "files": [
            {"file": r.file, "ok": r.ok, "diagnostics": [asdict(d) for d in r.diagnostics]} for r in results
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Emit machine-readable Diamond parser diagnostics.")
    ap.add_argument("--in", dest="in_path", required=True, help="Input .dmd file or directory")
    ap.add_argument("--out", dest="out_path", default=None, help="Optional JSON output path")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = ap.parse_args(argv)

    report = run(Path(args.in_path))
    payload = json.dumps(report, ensure_ascii=True, indent=(2 if args.pretty else None))

    if args.out_path:
        out = Path(args.out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
