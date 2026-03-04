#!/usr/bin/env python3
"""Autofix Diamond source to canonical v1 syntax."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


METHOD_DECL_RE = re.compile(
    r"^(?P<prefix>\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\()"
    r"(?P<params>[^)]*)"
    r"(?P<suffix>\).*)$"
)


@dataclass(frozen=True)
class RewriteStats:
    section_sigil_rewrites: int
    explicit_self_rewrites: int

    @property
    def changed(self) -> bool:
        return (self.section_sigil_rewrites + self.explicit_self_rewrites) > 0


def _iter_inputs(in_path: Path) -> list[Path]:
    if in_path.is_file():
        return [in_path] if in_path.suffix == ".dmd" else []
    return sorted(p for p in in_path.glob("*.dmd") if p.is_file())


def _split_line_comment_preserve_strings(line: str) -> tuple[str, str]:
    in_string = False
    escape = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if in_string:
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
            i += 1
            continue
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            return line[:i], line[i:]
        i += 1
    return line, ""


def _rewrite_section_sigil(source: str) -> tuple[str, int]:
    out: list[str] = []
    in_string = False
    escape = False
    in_comment = False
    rewrites = 0
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        if in_comment:
            out.append(ch)
            if ch == "\n":
                in_comment = False
            i += 1
            continue

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

        if ch == "/" and nxt == "/":
            out.append(ch)
            out.append(nxt)
            in_comment = True
            i += 2
            continue

        if ch == '"':
            out.append(ch)
            in_string = True
            i += 1
            continue

        if ch == "§":
            out.append("$")
            rewrites += 1
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out), rewrites


def _split_params(params: str) -> list[str]:
    if not params.strip():
        return []

    out: list[str] = []
    buf: list[str] = []
    depth = 0
    in_string = False
    escape = False

    for ch in params:
        if in_string:
            buf.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            buf.append(ch)
            continue

        if ch in "([{<":
            depth += 1
            buf.append(ch)
            continue

        if ch in ")]}>":
            depth = max(0, depth - 1)
            buf.append(ch)
            continue

        if ch == "," and depth == 0:
            out.append("".join(buf))
            buf = []
            continue

        buf.append(ch)

    out.append("".join(buf))
    return out


def _drop_explicit_self_param(params: str) -> tuple[str, bool]:
    parts = _split_params(params)
    if not parts:
        return params, False

    first = parts[0]
    if not re.match(r"^\s*self\s*:\s*.+$", first):
        return params, False

    if len(parts) == 1:
        return "", True

    kept = ",".join(parts[1:])
    return kept.lstrip(), True


def _rewrite_explicit_self_receiver(source: str) -> tuple[str, int]:
    rewrites = 0
    out_lines: list[str] = []
    for raw in source.splitlines(keepends=True):
        nl = "\n" if raw.endswith("\n") else ""
        line = raw[:-1] if nl else raw
        code, comment = _split_line_comment_preserve_strings(line)
        match = METHOD_DECL_RE.match(code)
        if not match:
            out_lines.append(line + nl)
            continue

        params = match.group("params")
        new_params, changed = _drop_explicit_self_param(params)
        if not changed:
            out_lines.append(line + nl)
            continue

        rewrites += 1
        new_code = f"{match.group('prefix')}{new_params}{match.group('suffix')}"
        out_lines.append(new_code + comment + nl)

    return "".join(out_lines), rewrites


def rewrite_source(source: str) -> tuple[str, RewriteStats]:
    step1, sigil_rewrites = _rewrite_section_sigil(source)
    step2, receiver_rewrites = _rewrite_explicit_self_receiver(step1)
    return step2, RewriteStats(sigil_rewrites, receiver_rewrites)


def rewrite_file(path: Path, write: bool) -> RewriteStats:
    src = path.read_text(encoding="utf-8")
    out, stats = rewrite_source(src)
    if write and stats.changed and out != src:
        path.write_text(out, encoding="utf-8")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate Diamond source to canonical v1 syntax.")
    ap.add_argument("--in", dest="inputs", action="append", required=True)
    ap.add_argument("--write", action="store_true", help="Write fixes in-place")
    args = ap.parse_args()

    files: list[Path] = []
    for raw in args.inputs:
        files.extend(_iter_inputs(Path(raw)))
    files = sorted(set(files))
    if not files:
        print("migrate_to_v1: no .dmd files found")
        return 0

    total_sigil = 0
    total_receiver = 0
    changed_files = 0
    for fp in files:
        stats = rewrite_file(fp, write=args.write)
        total_sigil += stats.section_sigil_rewrites
        total_receiver += stats.explicit_self_rewrites
        if stats.changed:
            changed_files += 1
            print(
                f"changed: {fp} "
                f"section_sigil={stats.section_sigil_rewrites} explicit_self={stats.explicit_self_rewrites}"
            )

    print(
        "migrate_to_v1: "
        f"files={len(files)} changed_files={changed_files} "
        f"section_sigil_rewrites={total_sigil} explicit_self_rewrites={total_receiver} "
        f"write={args.write}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
