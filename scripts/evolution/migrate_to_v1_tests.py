#!/usr/bin/env python3
"""Regression tests for Diamond v1 migration tool."""

from __future__ import annotations

from migrate_to_v1 import rewrite_source


def test_rewrite_section_sigil_and_receiver() -> None:
    src = '§C(x:I){{a:x}}\n.C.m(self:O)>I=#.a\n'
    out, stats = rewrite_source(src)
    if out != '$C(x:I){{a:x}}\n.C.m()>I=#.a\n':
        raise AssertionError(f"unexpected rewrite output: {out!r}")
    if stats.section_sigil_rewrites != 1 or stats.explicit_self_rewrites != 1:
        raise AssertionError(f"unexpected stats: {stats}")


def test_ignore_section_sigil_in_comment_and_string() -> None:
    src = '// § comment\nf()>S="§"\n'
    out, stats = rewrite_source(src)
    if out != src:
        raise AssertionError(f"expected no rewrite, got: {out!r}")
    if stats.changed:
        raise AssertionError(f"expected unchanged stats, got: {stats}")


def test_rewrite_self_with_remaining_params() -> None:
    src = '.C.m(self:O,x:I,y:S)>I=#.a\n'
    out, stats = rewrite_source(src)
    if out != '.C.m(x:I,y:S)>I=#.a\n':
        raise AssertionError(f"expected self removed, got: {out!r}")
    if stats.explicit_self_rewrites != 1:
        raise AssertionError(f"expected one self rewrite, got: {stats}")


def test_idempotent_rewrite() -> None:
    src = '$C(x:I){{a:x}}\n.C.m()>I=#.a\n'
    out1, stats1 = rewrite_source(src)
    out2, stats2 = rewrite_source(out1)
    if out1 != src or out2 != src:
        raise AssertionError("expected idempotent canonical output")
    if stats1.changed or stats2.changed:
        raise AssertionError(f"expected no changes, got: {stats1} {stats2}")


def main() -> int:
    tests = [
        ("rewrite_section_sigil_and_receiver", test_rewrite_section_sigil_and_receiver),
        ("ignore_section_sigil_in_comment_and_string", test_ignore_section_sigil_in_comment_and_string),
        ("rewrite_self_with_remaining_params", test_rewrite_self_with_remaining_params),
        ("idempotent_rewrite", test_idempotent_rewrite),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"migration regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
