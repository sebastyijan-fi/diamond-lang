#!/usr/bin/env python3
"""Regression tests for memory/runtime policy validator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validate_memory_runtime_policy import validate_policy


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_tree(root: Path) -> None:
    _write(root / "runtime/diamond_runtime.py", "def extern_call(symbol,args=None):\n    raise NotImplementedError\n")
    _write(
        root / "runtime/diamond_runtime.rs",
        "use std::panic;\npub fn extern_call(symbol:&str,args:Option<String>)->String{panic::catch_unwind(||\"x\".to_string()).ok();\"x\".to_string()}\n",
    )
    _write(root / "backends/rust_backend.py", "code='catch_unwind'\n")
    _write(
        root / "docs/object.md",
        "V1 does not define deterministic language-level destructors.\n"
        "single-thread semantic domain\n"
        "non-`Send`\n",
    )
    _write(
        root / "docs/sem.md",
        "Error Contract\nextern_call(symbol, args)\nsingle-thread domain\n",
    )
    _write(root / "docs/interop.md", "C ABI interop via extern and extern_call\n")
    _write(root / "cases/runtime.json", json.dumps({"cases": [{"id": "extern_call.stub"}, {"id": "try_catch.reraise"}]}))


def _valid_policy() -> dict[str, object]:
    return {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "memory_runtime": {
            "python_model": "gc",
            "js_model": "gc",
            "rust_model": "rc_refcell_compat",
            "manual_memory": False,
            "deterministic_destructor": False,
        },
        "safety_boundary": {
            "unsafe_language_surface": "none",
            "rust_unsafe_blocks_allowed": False,
            "audit_mode": "static_policy_gate",
        },
        "ffi_abi": {
            "c_abi_mode": "host_extern_bridge",
            "runtime_symbol": "extern_call",
            "default_behavior": "not_implemented",
        },
        "refs": {
            "python_runtime": "runtime/diamond_runtime.py",
            "rust_runtime": "runtime/diamond_runtime.rs",
            "rust_backend": "backends/rust_backend.py",
            "object_contract": "docs/object.md",
            "semantic_contract": "docs/sem.md",
            "interop_policy": "docs/interop.md",
            "conformance_cases": "cases/runtime.json",
        },
        "conformance": {"required_case_ids": ["extern_call.stub"]},
    }


def test_accept_valid_policy() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        errors = validate_policy(_valid_policy(), root)
        if errors:
            raise AssertionError(f"expected no errors, got: {errors}")


def test_reject_unsafe_block() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        _write(
            root / "runtime/diamond_runtime.rs",
            "pub fn extern_call(symbol:&str,args:Option<String>)->String{unsafe {\"x\".to_string()}}\n",
        )
        errors = validate_policy(_valid_policy(), root)
        if not any("disallowed unsafe block" in err for err in errors):
            raise AssertionError(f"expected unsafe block error, got: {errors}")


def test_reject_missing_case_id() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        policy = _valid_policy()
        conf = policy["conformance"]
        if not isinstance(conf, dict):
            raise AssertionError("invalid test policy conformance")
        conf["required_case_ids"] = ["extern_call.stub", "missing.case"]
        errors = validate_policy(policy, root)
        if not any("missing required case id" in err for err in errors):
            raise AssertionError(f"expected missing case id error, got: {errors}")


def main() -> int:
    tests = [
        ("accept_valid_policy", test_accept_valid_policy),
        ("reject_unsafe_block", test_reject_unsafe_block),
        ("reject_missing_case_id", test_reject_missing_case_id),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"memory policy regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
