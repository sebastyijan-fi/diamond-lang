#!/usr/bin/env python3
"""Regression tests for excluded-scope policy validator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from validate_scope_policy import validate_policy


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_policy() -> dict[str, object]:
    return {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "scope": {
            "metaprogramming": "none",
            "reflection_codegen": "none",
            "effect_system": "none",
            "inheritance_traits": "none",
            "ide_debug_profiler": "none",
        },
        "enforcement": {
            "grammar_ref": "src/transpiler/grammar.py",
            "semantic_contract_ref": "docs/sem.md",
            "object_contract_ref": "docs/obj.md",
            "tooling_policy_ref": "docs/tooling.md",
            "banned_tokens": ["macro", "effect", "extends", "trait"],
        },
    }


def _seed_tree(root: Path) -> None:
    _write(root / "src/transpiler/grammar.py", 'DIAMOND_GRAMMAR = "start: IDENT"')
    _write(
        root / "docs/sem.md",
        "\n".join(
            [
                "Macro/annotation/compile-time-eval syntax is out-of-profile in v1.",
                "Reflection/source-generation syntax is out-of-profile in v1.",
                "Effect typing/algebraic-effects syntax is out-of-profile in v1.",
            ]
        )
        + "\n",
    )
    _write(
        root / "docs/obj.md",
        "\n".join(
            [
                "Classical class inheritance is out-of-profile for V1.",
                "Trait/interface system is out-of-profile for V1.",
            ]
        )
        + "\n",
    )
    _write(
        root / "docs/tooling.md",
        "\n".join(
            [
                "LSP integration is out-of-profile in V1.",
                "Interactive debugger integration is out-of-profile in V1.",
                "Profiler integration is out-of-profile in V1.",
            ]
        )
        + "\n",
    )
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
        _write(root / "samples/bad.dmd", "macro x(y:I)>I=y\n")
        errors = validate_policy(_valid_policy(), root, [root / "samples"])
        if not any("out-of-profile scope token" in err for err in errors):
            raise AssertionError(f"expected banned token error, got: {errors}")


def test_reject_missing_tooling_clause() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_tree(root)
        _write(root / "docs/tooling.md", "tooling notes\n")
        errors = validate_policy(_valid_policy(), root, [root / "samples"])
        if not any("tooling policy missing clause" in err for err in errors):
            raise AssertionError(f"expected tooling clause error, got: {errors}")


def main() -> int:
    tests = [
        ("accept_valid_policy", test_accept_valid_policy),
        ("reject_banned_token_in_source", test_reject_banned_token_in_source),
        ("reject_missing_tooling_clause", test_reject_missing_tooling_clause),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"scope policy regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
