#!/usr/bin/env python3
"""Regression tests for canonical syntax validator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from validate_canonical_syntax import validate_file


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def test_accept_canonical() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _write(
            Path(td),
            "ok.dmd",
            "$C(x:I){{a:x}}\n.C.m()>I=#.a\n",
        )
        got = validate_file(path)
        if got:
            raise AssertionError(f"expected no violations, got: {got}")


def test_reject_section_sigil() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _write(Path(td), "bad_sigil.dmd", "§C(x:I){{a:x}}\n")
        got = validate_file(path)
        if not any("class sigil" in v.message for v in got):
            raise AssertionError(f"expected class sigil violation, got: {got}")


def test_reject_explicit_self_receiver() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _write(Path(td), "bad_self.dmd", ".C.m(self:O)>I=#.x\n")
        got = validate_file(path)
        if not any("receiver parameter" in v.message for v in got):
            raise AssertionError(f"expected explicit self violation, got: {got}")


def test_ignore_section_in_comment_and_string() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _write(
            Path(td),
            "ok_comment_string.dmd",
            '// § in comment\nf()>S="§"\n',
        )
        got = validate_file(path)
        if got:
            raise AssertionError(f"expected no violations, got: {got}")


def main() -> int:
    tests = [
        ("accept_canonical", test_accept_canonical),
        ("reject_section_sigil", test_reject_section_sigil),
        ("reject_explicit_self_receiver", test_reject_explicit_self_receiver),
        ("ignore_section_in_comment_and_string", test_ignore_section_in_comment_and_string),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"canonical syntax regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
