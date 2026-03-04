#!/usr/bin/env python3
"""Validate Diamond source against canonical syntax profile.

Canonical v1 profile (measured):
- class sigil: `$` (reject `§`)
- implicit receiver in methods (reject explicit `self:...` receiver params)
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

METHOD_EXPLICIT_SELF_RE = re.compile(
    r"^\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\(\s*self\s*:"
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    col: int
    message: str


def _iter_inputs(in_path: Path) -> list[Path]:
    if in_path.is_file():
        return [in_path] if in_path.suffix == ".dmd" else []
    return sorted(p for p in in_path.glob("*.dmd") if p.is_file())


def _strip_line_comment_preserve_strings(line: str) -> str:
    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _find_disallowed_section_sigil(source: str, path: Path) -> list[Violation]:
    violations: list[Violation] = []
    in_string = False
    escape = False
    in_comment = False
    line = 1
    col = 1
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if in_comment:
            if ch == "\n":
                in_comment = False
            i += 1
            line = line + 1 if ch == "\n" else line
            col = 1 if ch == "\n" else col + 1
            continue
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            line = line + 1 if ch == "\n" else line
            col = 1 if ch == "\n" else col + 1
            continue
        if ch == "/" and nxt == "/":
            in_comment = True
            i += 2
            col += 2
            continue
        if ch == '"':
            in_string = True
            i += 1
            col += 1
            continue
        if ch == "§":
            violations.append(
                Violation(
                    path=path,
                    line=line,
                    col=col,
                    message="non-canonical class sigil '§' (use '$')",
                )
            )
        i += 1
        line = line + 1 if ch == "\n" else line
        col = 1 if ch == "\n" else col + 1
    return violations


def _find_explicit_self_methods(source: str, path: Path) -> list[Violation]:
    violations: list[Violation] = []
    for idx, raw in enumerate(source.splitlines(), start=1):
        line = _strip_line_comment_preserve_strings(raw)
        if METHOD_EXPLICIT_SELF_RE.search(line):
            violations.append(
                Violation(
                    path=path,
                    line=idx,
                    col=1,
                    message="explicit receiver parameter is non-canonical (receiver is implicit; use `#` binder)",
                )
            )
    return violations


def validate_file(path: Path) -> list[Violation]:
    src = path.read_text(encoding="utf-8")
    out: list[Violation] = []
    out.extend(_find_disallowed_section_sigil(src, path))
    out.extend(_find_explicit_self_methods(src, path))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate canonical Diamond syntax.")
    ap.add_argument("--in", dest="inputs", action="append", required=True)
    ap.add_argument(
        "--experimental-mode",
        action="store_true",
        help="Allow non-canonical syntax (report as warnings only)",
    )
    args = ap.parse_args()

    env_experimental = os.environ.get("DIAMOND_EXPERIMENTAL_SYNTAX", "0") == "1"
    experimental = args.experimental_mode or env_experimental

    files: list[Path] = []
    for raw in args.inputs:
        files.extend(_iter_inputs(Path(raw)))
    files = sorted(set(files))
    if not files:
        print("canonical_syntax: no .dmd files found")
        return 0

    violations: list[Violation] = []
    for fp in files:
        violations.extend(validate_file(fp))

    print(f"canonical_syntax: files={len(files)} violations={len(violations)} experimental={experimental}")
    for v in violations:
        level = "warning" if experimental else "error"
        print(f"{level}: {v.path}:{v.line}:{v.col}: {v.message}")

    if violations and not experimental:
        print("FAIL: canonical syntax validation failed")
        return 1
    print("OK: canonical syntax validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
