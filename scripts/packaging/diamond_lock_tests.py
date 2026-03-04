#!/usr/bin/env python3
"""Regression tests for Diamond lockfile generator/validator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from diamond_lock import build_lock
from validate_diamond_lock import validate_lock


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_deterministic_order_and_digest() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "b.dmd", "g()>I=2\n")
        _write(root / "a.dmd", "f()>I=1\n")
        files = [root / "b.dmd", root / "a.dmd"]
        lock1 = build_lock(files, root)
        lock2 = build_lock(list(reversed(files)), root)
        if lock1 != lock2:
            raise AssertionError("expected deterministic lock regardless of input order")
        names = [m["path"] for m in lock1["modules"]]  # type: ignore[index]
        if names != ["a.dmd", "b.dmd"]:
            raise AssertionError(f"unexpected deterministic path order: {names}")


def test_validate_lock_ok() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "x.dmd", "x()>I=1\n")
        files = [root / "x.dmd"]
        lock = build_lock(files, root)
        lock_path = root / "diamond.lock.json"
        lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        errors = validate_lock(lock_path, files, root)
        if errors:
            raise AssertionError(f"expected no validation errors, got: {errors}")


def test_validate_lock_detects_change() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "x.dmd", "x()>I=1\n")
        files = [root / "x.dmd"]
        lock = build_lock(files, root)
        lock_path = root / "diamond.lock.json"
        lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        _write(root / "x.dmd", "x()>I=2\n")
        errors = validate_lock(lock_path, files, root)
        if not any("source_digest mismatch" in err for err in errors):
            raise AssertionError(f"expected source_digest mismatch, got: {errors}")


def main() -> int:
    tests = [
        ("deterministic_order_and_digest", test_deterministic_order_and_digest),
        ("validate_lock_ok", test_validate_lock_ok),
        ("validate_lock_detects_change", test_validate_lock_detects_change),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"diamond lock regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
