#!/usr/bin/env python3
"""Regression tests for concurrency policy validator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from validate_concurrency_policy import validate_policy


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_policy() -> dict[str, object]:
    return {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "concurrency": {
            "semantic_domain": "single_thread",
            "async_support": "none",
            "memory_ordering": "none",
            "cancellation": "none",
            "structured_concurrency": False,
        },
        "enforcement": {
            "grammar_ref": "src/transpiler/grammar.py",
            "semantic_contract_ref": "docs/sem.md",
            "object_contract_ref": "docs/obj.md",
            "banned_tokens": [
                "async",
                "await",
                "yield",
                "thread",
                "mutex",
                "atomic",
                "channel",
                "spawn",
            ],
        },
    }


def _seed_tree(root: Path) -> None:
    _write(root / "src/transpiler/grammar.py", 'DIAMOND_GRAMMAR = "start: IDENT"')
    _write(root / "docs/sem.md", "# Semantics\n## Concurrency scope\nsingle-thread only\n")
    _write(root / "docs/obj.md", "V1 object contract uses single-thread semantic domain.\n")
    _write(root / "samples/ok.dmd", "f(x:I)>I=x+1\n")


def test_accept_valid_policy() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        errors = validate_policy(_valid_policy(), root, [root / "samples"])
        if errors:
            raise AssertionError(f"expected no errors, got: {errors}")


def test_reject_banned_token_in_source() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        _write(root / "samples/bad.dmd", "worker()>I=async(task)\n")
        errors = validate_policy(_valid_policy(), root, [root / "samples"])
        if not any("out-of-profile concurrency token" in err for err in errors):
            raise AssertionError(f"expected banned token error, got: {errors}")


def test_reject_missing_single_thread_clause() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        _write(root / "docs/obj.md", "object contract\n")
        errors = validate_policy(_valid_policy(), root, [root / "samples"])
        if not any("single-thread semantic domain" in err for err in errors):
            raise AssertionError(f"expected single-thread clause error, got: {errors}")


def main() -> int:
    tests = [
        ("accept_valid_policy", test_accept_valid_policy),
        ("reject_banned_token_in_source", test_reject_banned_token_in_source),
        ("reject_missing_single_thread_clause", test_reject_missing_single_thread_clause),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"concurrency policy regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
