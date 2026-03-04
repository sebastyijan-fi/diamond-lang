#!/usr/bin/env python3
"""Regression checks for static capability composition validation."""

from __future__ import annotations

from parse_to_ir import parse_source
from capability_validate import validate_program_capabilities


def _report(src: str):
    prog = parse_source(src, module_name="cap_tests.dmd")
    return validate_program_capabilities(prog)


def test_transitive_union() -> None:
    src = (
        "h^(c,db)(x:I)>I=1\n"
        "g^(c,db,net)(x:I)>I=h(x)\n"
        "f^(c,db,net)(x:I)>I=g(x)\n"
    )
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"expected no errors, got {rep.errors}")


def test_restriction_missing_capability() -> None:
    src = (
        "g^(c,net)(x:I)>I=slp(0);1\n"
        "f^(c,db)(x:I)>I=g(x)\n"
    )
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected missing capability error")
    msg = "\n".join(rep.errors)
    if "missing required" not in msg or "time_sleep" not in msg:
        raise AssertionError(f"unexpected error text: {msg}")


def test_inference_only_mode() -> None:
    src = "f()>I=slp(0);1"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"expected no errors, got {rep.errors}")
    if not rep.warnings:
        raise AssertionError("expected inference-only warning")


def test_unused_declared_warning() -> None:
    src = "f^(c,net,db)()>I=1"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"expected no errors, got {rep.errors}")
    if not any("include unused" in w for w in rep.warnings):
        raise AssertionError(f"expected unused-cap warning, got {rep.warnings}")


def test_method_self_call_transitive_capability() -> None:
    src = (
        "$Worker(v:I){{}}\n"
        ".Worker.io()>I=slp(0)\n"
        ".Worker.run^(db)()>I=#.io()\n"
    )
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected missing capability error on method self-call")
    msg = "\n".join(rep.errors)
    if "Worker__run" not in msg or "missing required" not in msg or "time_sleep" not in msg:
        raise AssertionError(f"unexpected error text: {msg}")


def test_class_only_decls_do_not_error() -> None:
    src = '$Only(x:I){{"tag":"v"}}'
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"expected no errors, got {rep.errors}")
    if rep.warnings:
        raise AssertionError(f"expected no warnings, got {rep.warnings}")


def main() -> int:
    tests = [
        ("transitive_union", test_transitive_union),
        ("restriction_missing_capability", test_restriction_missing_capability),
        ("inference_only_mode", test_inference_only_mode),
        ("unused_declared_warning", test_unused_declared_warning),
        ("method_self_call_transitive_capability", test_method_self_call_transitive_capability),
        ("class_only_decls_do_not_error", test_class_only_decls_do_not_error),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"capability validation regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
