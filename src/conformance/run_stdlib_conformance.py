#!/usr/bin/env python3
"""Run stdlib/runtime conformance cases against diamond_runtime."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable


def _load_runtime(module_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("diamond_runtime_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load runtime module from {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fn_library(dm: Any) -> dict[str, Callable[..., Any]]:
    def sum2(a: Any, b: Any) -> Any:
        return a + b

    def concat2(a: str, b: str) -> str:
        return f"{a},{b}" if a else b

    def add_ab_c(a: int, b: int, c: int = 0) -> int:
        return a + b + c

    def const_5() -> int:
        return 5

    def raise_value_error() -> Any:
        raise ValueError("boom")

    def handler_msg(exc: Exception) -> str:
        return f"handled:{exc}"

    def handler_reraise(exc: Exception) -> Any:
        _ = exc
        return dm.RERAISE

    def handler_type(exc: Exception) -> str:
        return f"caught:{type(exc).__name__}"

    def try_handle_via_runtime() -> Any:
        return dm.try_catch(lambda: raise_value_error(), handler_msg)

    def try_reraise_via_runtime() -> Any:
        return dm.try_catch(lambda: raise_value_error(), handler_reraise)

    def propagate_raised() -> Any:
        return dm.propagate(lambda: raise_value_error())

    def cap_allow_all_ok() -> str:
        dm.set_capability_policy("allow_all", [])
        dm.cap_check("cap_allow_all_ok", ["c", "net"])
        return "ok"

    def cap_allow_list_ok() -> str:
        dm.set_capability_policy("allow_list", ["net", "fs"])
        dm.cap_check("cap_allow_list_ok", ["c", "net"])
        return "ok"

    def cap_allow_list_fail() -> Any:
        dm.set_capability_policy("allow_list", ["fs"])
        dm.cap_check("cap_allow_list_fail", ["c", "net"])
        return "unreachable"

    def obj_alias_identity_true() -> bool:
        base = dm.obj_new({"x": 1})
        a = base
        b = base
        return dm.obj_is(a, b)

    def obj_alias_mutation_visible() -> int:
        base = dm.obj_new({"x": 1})
        a = base
        b = base
        dm.obj_set(a, "x", 9)
        return dm.obj_get(b, "x")

    def obj_closed_shape_set_missing() -> Any:
        base = dm.obj_new({"x": 1})
        dm.obj_set(base, "y", 2)
        return "unreachable"

    def obj_get_missing_field() -> Any:
        base = dm.obj_new({"x": 1})
        return dm.obj_get(base, "y")

    def obj_eq_structural_true() -> bool:
        left = dm.obj_new({"x": 1, "tags": ["a", "b"]})
        right = dm.obj_new({"x": 1, "tags": ["a", "b"]})
        return dm.obj_eq(left, right)

    def obj_eq_structural_false() -> bool:
        left = dm.obj_new({"x": 1, "tags": ["a", "b"]})
        right = dm.obj_new({"x": 2, "tags": ["a", "b"]})
        return dm.obj_eq(left, right)

    def obj_eq_cycle_true() -> bool:
        left = dm.obj_new({"n": 1, "next": None})
        right = dm.obj_new({"n": 1, "next": None})
        dm.obj_set(left, "next", left)
        dm.obj_set(right, "next", right)
        return dm.obj_eq(left, right)

    def obj_eq_cycle_false() -> bool:
        left = dm.obj_new({"n": 1, "next": None})
        right = dm.obj_new({"n": 2, "next": None})
        dm.obj_set(left, "next", left)
        dm.obj_set(right, "next", right)
        return dm.obj_eq(left, right)

    def obj_invoke_method_ok() -> int:
        def Point__inc(self: Any, d: int) -> int:
            dm.obj_set(self, "x", dm.obj_get(self, "x") + d)
            return dm.obj_get(self, "x")

        scope = {"Point__inc": Point__inc}
        p = dm.obj_new({"x": 1}, class_name="Point")
        return dm.obj_invoke(scope, p, "inc", [2])

    def obj_invoke_missing_method() -> Any:
        p = dm.obj_new({"x": 1}, class_name="Point")
        return dm.obj_invoke({}, p, "inc", [2])

    def obj_invoke_fallback_member() -> int:
        holder = SimpleNamespace(add=lambda x: x + 3)
        return dm.obj_invoke({}, holder, "add", [2])

    def obj_json_dumps() -> str:
        base = dm.obj_new({"x": 1, "tags": [2, 3]}, class_name="Point")
        return dm.json_dumps(base)

    def dt_date_iso() -> str:
        return dm.dt_date(2024, 2, 9).isoformat()

    def dt_datetime_iso() -> str:
        return dm.dt_datetime(2024, 2, 9, 10, 11, 12, 13000, dm.tz_utc()).isoformat()

    def dt_time_iso() -> str:
        return dm.dt_time(10, 11, 12, 13000).isoformat()

    def tz_utc_str() -> str:
        return str(dm.tz_utc())

    def tz_offset_str() -> str:
        return str(dm.tz_offset(2, 30))

    def pad6_basic() -> str:
        return dm.pad6("42")

    def parse_int_base_hex() -> int:
        return dm.parse_int_base("ff", 16)

    return {
        "sum2": sum2,
        "concat2": concat2,
        "add_ab_c": add_ab_c,
        "const_5": const_5,
        "raise_value_error": raise_value_error,
        "handler_msg": handler_msg,
        "handler_reraise": handler_reraise,
        "handler_type": handler_type,
        "try_handle_via_runtime": try_handle_via_runtime,
        "try_reraise_via_runtime": try_reraise_via_runtime,
        "propagate_raised": propagate_raised,
        "cap_allow_all_ok": cap_allow_all_ok,
        "cap_allow_list_ok": cap_allow_list_ok,
        "cap_allow_list_fail": cap_allow_list_fail,
        "obj_alias_identity_true": obj_alias_identity_true,
        "obj_alias_mutation_visible": obj_alias_mutation_visible,
        "obj_closed_shape_set_missing": obj_closed_shape_set_missing,
        "obj_get_missing_field": obj_get_missing_field,
        "obj_eq_structural_true": obj_eq_structural_true,
        "obj_eq_structural_false": obj_eq_structural_false,
        "obj_eq_cycle_true": obj_eq_cycle_true,
        "obj_eq_cycle_false": obj_eq_cycle_false,
        "obj_invoke_method_ok": obj_invoke_method_ok,
        "obj_invoke_missing_method": obj_invoke_missing_method,
        "obj_invoke_fallback_member": obj_invoke_fallback_member,
        "obj_json_dumps": obj_json_dumps,
        "dt_date_iso": dt_date_iso,
        "dt_datetime_iso": dt_datetime_iso,
        "dt_time_iso": dt_time_iso,
        "tz_utc_str": tz_utc_str,
        "tz_offset_str": tz_offset_str,
        "pad6_basic": pad6_basic,
        "parse_int_base_hex": parse_int_base_hex,
    }


def _decode(value: Any, fns: dict[str, Callable[..., Any]]) -> Any:
    if isinstance(value, list):
        return [_decode(v, fns) for v in value]
    if isinstance(value, dict):
        if "$fn" in value:
            fn_name = value["$fn"]
            if fn_name not in fns:
                raise ValueError(f"unknown fn fixture: {fn_name}")
            return fns[fn_name]
        if "$tuple" in value:
            return tuple(_decode(v, fns) for v in value["$tuple"])
        if "$obj" in value:
            payload = value["$obj"]
            if not isinstance(payload, dict):
                raise ValueError("$obj payload must be an object")
            attrs = payload.get("attrs", {})
            if not isinstance(attrs, dict):
                raise ValueError("$obj.attrs must be an object")
            return SimpleNamespace(**{k: _decode(v, fns) for k, v in attrs.items()})
        return {k: _decode(v, fns) for k, v in value.items()}
    return value


def _canon(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_canon(v) for v in value]
    if isinstance(value, list):
        return [_canon(v) for v in value]
    if isinstance(value, dict):
        if all(isinstance(k, str) for k in value):
            return {k: _canon(v) for k, v in value.items()}
        items = [[_canon(k), _canon(v)] for k, v in value.items()]
        items.sort(key=lambda it: json.dumps(it[0], sort_keys=True, ensure_ascii=True))
        return items
    if isinstance(value, SimpleNamespace):
        return {"$obj": {"attrs": {k: _canon(v) for k, v in vars(value).items()}}}
    return value


def _iter_cases(cases_dir: Path) -> list[tuple[str, dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any]]] = []
    for fp in sorted(cases_dir.glob("*.json")):
        payload = json.loads(fp.read_text(encoding="utf-8"))
        case_list = payload.get("cases")
        if not isinstance(case_list, list):
            raise ValueError(f"{fp}: expected top-level 'cases' list")
        for case in case_list:
            if not isinstance(case, dict):
                raise ValueError(f"{fp}: each case must be an object")
            out.append((fp.name, case))
    return out


def _run_case(
    dm: Any,
    case: dict[str, Any],
    fns: dict[str, Callable[..., Any]],
) -> tuple[bool, str]:
    case_id = str(case.get("id", "<missing-id>"))
    fn_name = case.get("fn")
    if not isinstance(fn_name, str):
        return False, f"{case_id}: missing fn name"
    if not hasattr(dm, fn_name):
        return False, f"{case_id}: runtime missing fn={fn_name}"

    fn = getattr(dm, fn_name)
    if hasattr(dm, "reset_capability_policy"):
        dm.reset_capability_policy()
    args = [_decode(a, fns) for a in case.get("args", [])]
    kwargs = {k: _decode(v, fns) for k, v in case.get("kwargs", {}).items()}
    expect = _decode(case.get("expect"), fns) if "expect" in case else None
    expect_error = case.get("expect_error")
    immut_idx = case.get("assert_args_unchanged", [])
    snapshots: dict[int, Any] = {}
    for idx in immut_idx:
        if not isinstance(idx, int) or idx < 0 or idx >= len(args):
            return False, f"{case_id}: invalid assert_args_unchanged index={idx}"
        snapshots[idx] = copy.deepcopy(args[idx])

    try:
        got = fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        if not isinstance(expect_error, dict):
            return False, f"{case_id}: unexpected error {type(exc).__name__}: {exc}"
        exp_type = expect_error.get("type")
        exp_contains = expect_error.get("contains")
        if exp_type is not None and type(exc).__name__ != exp_type:
            return False, f"{case_id}: error type {type(exc).__name__} != {exp_type}"
        if exp_contains is not None and str(exp_contains) not in str(exc):
            return False, f"{case_id}: error message missing substring {exp_contains!r}: {exc!r}"
        return True, f"{case_id}: pass(error {type(exc).__name__})"

    if expect_error is not None:
        return False, f"{case_id}: expected error but got value {got!r}"

    if _canon(got) != _canon(expect):
        return False, f"{case_id}: value mismatch got={_canon(got)!r} expected={_canon(expect)!r}"

    for idx, before in snapshots.items():
        if _canon(args[idx]) != _canon(before):
            return False, f"{case_id}: arg[{idx}] mutated; before={_canon(before)!r} after={_canon(args[idx])!r}"

    return True, f"{case_id}: pass"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run Diamond stdlib conformance cases.")
    ap.add_argument(
        "--runtime",
        default="src/transpiler/runtime/diamond_runtime.py",
        help="Path to runtime module under test",
    )
    ap.add_argument(
        "--cases-dir",
        default="src/conformance/cases",
        help="Directory containing conformance case JSON files",
    )
    ap.add_argument("--fail-fast", action="store_true")
    args = ap.parse_args(argv)

    runtime_path = Path(args.runtime).resolve()
    cases_dir = Path(args.cases_dir).resolve()
    if not runtime_path.is_file():
        print(f"runtime module not found: {runtime_path}")
        return 2
    if not cases_dir.is_dir():
        print(f"cases directory not found: {cases_dir}")
        return 2

    dm = _load_runtime(runtime_path)
    fns = _fn_library(dm)
    cases = _iter_cases(cases_dir)
    if not cases:
        print("no conformance cases found")
        return 2

    passed = 0
    failed = 0
    print("file,case,result")
    for file_name, case in cases:
        ok, msg = _run_case(dm, case, fns)
        case_id = str(case.get("id", "<missing-id>"))
        if ok:
            passed += 1
            print(f"{file_name},{case_id},PASS")
        else:
            failed += 1
            print(f"{file_name},{case_id},FAIL")
            print(f"  detail: {msg}")
            if args.fail_fast:
                break

    total = passed + failed
    print(f"\nsummary: {passed}/{total} passing")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
