#!/usr/bin/env python3
"""Regression checks for class/method emission across backends."""

from __future__ import annotations

from backends import get_backend
from parse_to_ir import parse_source


SOURCE = """$Point(x:I,y:I){{sum:#.x+#.y}}
.Point.inc(d:I)>I=#.x+d
main()>I=Point(1,2).inc(3)
"""

MATCH_CAPTURE_SOURCE = """f(x:I)>I=x~1:1~v:v
"""


def _emit(backend: str) -> str:
    _, emit = get_backend(backend)
    program = parse_source(SOURCE, module_name="backend_object_regressions.dmd")
    return emit(program)


def test_python_backend() -> None:
    out = _emit("python")
    if "def Point(" not in out:
        raise AssertionError("python backend missing class ctor")
    if "def Point__inc(" not in out:
        raise AssertionError("python backend missing mangled method")
    if "dm.obj_invoke(" not in out:
        raise AssertionError("python backend missing object invoke lowering")


def test_js_backend() -> None:
    out = _emit("js")
    if "export function Point(" not in out:
        raise AssertionError("js backend missing class ctor")
    if "export function Point__inc(" not in out:
        raise AssertionError("js backend missing mangled method")
    if "dm.obj_invoke(__dm_scope" not in out:
        raise AssertionError("js backend missing object invoke lowering")


def test_rust_backend() -> None:
    out = _emit("rust")
    if "pub fn Point(" not in out:
        raise AssertionError("rust backend missing class ctor")
    if "pub fn Point__inc(" not in out:
        raise AssertionError("rust backend missing mangled method")
    if "__dm_obj_invoke(" not in out:
        raise AssertionError("rust backend missing object invoke helper")


def test_wasm_backend() -> None:
    out = _emit("wasm")
    if "export function Point(" not in out:
        raise AssertionError("wasm backend parity output missing class ctor")


def _emit_match_capture(backend: str) -> str:
    _, emit = get_backend(backend)
    program = parse_source(MATCH_CAPTURE_SOURCE, module_name="backend_match_capture_regressions.dmd")
    return emit(program)


def test_python_match_capture_emits_runtime_marker() -> None:
    out = _emit_match_capture("python")
    if "lambda v:" not in out:
        raise AssertionError("python backend should emit capture lambda for match arm")
    if "dm.CAPTURE('v')" not in out:
        raise AssertionError("python backend should emit CAPTURE marker")


def test_js_match_capture_emits_runtime_marker() -> None:
    out = _emit_match_capture("js")
    if "(v) =>" not in out:
        raise AssertionError("js backend should emit capture lambda parameter")
    if "dm.capture('v')" not in out and 'dm.capture("v")' not in out:
        raise AssertionError("js backend should emit capture marker")


def test_rust_match_capture_emits_runtime_binding() -> None:
    out = _emit_match_capture("rust")
    if "let v = __dm_subject.clone()" not in out:
        raise AssertionError("rust backend should bind capture name from match subject")


def main() -> int:
    tests = [
        ("python_backend", test_python_backend),
        ("js_backend", test_js_backend),
        ("rust_backend", test_rust_backend),
        ("wasm_backend", test_wasm_backend),
        ("python_match_capture_emits_runtime_marker", test_python_match_capture_emits_runtime_marker),
        ("js_match_capture_emits_runtime_marker", test_js_match_capture_emits_runtime_marker),
        ("rust_match_capture_emits_runtime_binding", test_rust_match_capture_emits_runtime_binding),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"backend object regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
