#!/usr/bin/env python3
"""Regression tests for panic/cleanup policy validator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validate_panic_cleanup_policy import validate_policy


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_tree(root: Path) -> None:
    _write(
        root / "runtime/diamond_runtime.py",
        "RERAISE=object()\n"
        "def try_catch(body,handler):\n    return body()\n"
        "def propagate(v):\n    return v\n",
    )
    _write(
        root / "docs/sem.md",
        "## 4) Error Contract\ntry(body, e: handler)\nreraise\n",
    )
    _write(
        root / "cases/runtime.json",
        json.dumps(
            {
                "cases": [
                    {"id": "try_catch.handle"},
                    {"id": "try_catch.reraise"},
                    {"id": "propagate.error"},
                ]
            }
        ),
    )


def _valid_policy() -> dict[str, object]:
    return {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "panic_cleanup": {
            "panic_mode": "exception_channel",
            "cleanup_model": "try_catch_handler",
            "reraise_sentinel": "RERAISE",
        },
        "runtime_refs": {
            "python_runtime": "runtime/diamond_runtime.py",
            "semantic_contract": "docs/sem.md",
        },
        "conformance": {
            "cases_file": "cases/runtime.json",
            "required_case_ids": [
                "try_catch.handle",
                "try_catch.reraise",
                "propagate.error",
            ],
        },
    }


def test_accept_valid_policy() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        errors = validate_policy(_valid_policy(), root)
        if errors:
            raise AssertionError(f"expected no errors, got: {errors}")


def test_reject_missing_runtime_symbol() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        _write(root / "runtime/diamond_runtime.py", "def propagate(v):\n    return v\n")
        errors = validate_policy(_valid_policy(), root)
        if not any("try_catch" in err for err in errors):
            raise AssertionError(f"expected try_catch symbol error, got: {errors}")


def test_reject_missing_case_id() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        policy = _valid_policy()
        conf = policy["conformance"]
        if not isinstance(conf, dict):
            raise AssertionError("invalid test conformance policy")
        conf["required_case_ids"] = ["try_catch.over.propagate"]
        errors = validate_policy(policy, root)
        if not any("missing required case id" in err for err in errors):
            raise AssertionError(f"expected missing case id error, got: {errors}")


def main() -> int:
    tests = [
        ("accept_valid_policy", test_accept_valid_policy),
        ("reject_missing_runtime_symbol", test_reject_missing_runtime_symbol),
        ("reject_missing_case_id", test_reject_missing_case_id),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"panic policy regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
