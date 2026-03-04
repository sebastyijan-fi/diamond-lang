#!/usr/bin/env python3
"""Regression tests for equality/identity/hash contract validator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validate_equality_contract import validate_contract


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_runtime(root: Path) -> None:
    _write(root / "runtime/diamond_runtime.py", "def obj_is(a,b):\n    return a is b\ndef obj_eq(a,b):\n    return a==b\n")
    _write(
        root / "runtime/diamond_runtime.js",
        "export function obj_is(a,b){return a===b;}\nexport function obj_eq(a,b){return a===b;}\n",
    )
    _write(
        root / "cases/runtime_v0_core.json",
        json.dumps(
            {
                "cases": [
                    {"id": "obj.alias.identity_true"},
                    {"id": "obj.eq.structural_true"},
                    {"id": "obj.eq.cycle_true"},
                ]
            }
        ),
    )


def _valid_contract() -> dict[str, object]:
    return {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "equality": {"mode": "structural_deep_cycle_safe"},
        "identity": {"mode": "reference"},
        "hash": {"objects": "unhashable", "scalars_stable": True},
        "runtime_refs": {
            "python": "runtime/diamond_runtime.py",
            "js": "runtime/diamond_runtime.js",
        },
        "conformance": {
            "cases_file": "cases/runtime_v0_core.json",
            "required_case_ids": [
                "obj.alias.identity_true",
                "obj.eq.structural_true",
                "obj.eq.cycle_true",
            ],
        },
    }


def test_accept_valid_contract() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_runtime(root)
        errors = validate_contract(_valid_contract(), root)
        if errors:
            raise AssertionError(f"expected no errors, got: {errors}")


def test_reject_missing_runtime_symbol() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_runtime(root)
        _write(root / "runtime/diamond_runtime.py", "def obj_is(a,b):\n    return a is b\n")
        errors = validate_contract(_valid_contract(), root)
        if not any("obj_eq" in err for err in errors):
            raise AssertionError(f"expected obj_eq error, got: {errors}")


def test_reject_missing_case_id() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_runtime(root)
        contract = _valid_contract()
        conf = contract["conformance"]
        if not isinstance(conf, dict):
            raise AssertionError("invalid test conformance contract")
        conf["required_case_ids"] = ["obj.eq.structural_false"]
        errors = validate_contract(contract, root)
        if not any("missing required case id" in err for err in errors):
            raise AssertionError(f"expected missing case id error, got: {errors}")


def main() -> int:
    tests = [
        ("accept_valid_contract", test_accept_valid_contract),
        ("reject_missing_runtime_symbol", test_reject_missing_runtime_symbol),
        ("reject_missing_case_id", test_reject_missing_case_id),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"equality contract regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
