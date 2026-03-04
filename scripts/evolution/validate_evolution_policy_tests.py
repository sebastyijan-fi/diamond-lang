#!/usr/bin/env python3
"""Regression tests for evolution policy validator."""

from __future__ import annotations

from validate_evolution_policy import validate_policy


def test_accept_valid_policy() -> None:
    valid = {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "deprecations": [
            {
                "id": "class_sigil_section",
                "since": "v1",
                "severity": "error",
                "replacement": "$",
                "autofix": True,
            },
            {
                "id": "explicit_self_receiver",
                "since": "v1",
                "severity": "error",
                "replacement": "implicit receiver with # binder",
                "autofix": True,
            },
        ],
        "migration": {
            "tool": "scripts/evolution/migrate_to_v1.py",
            "min_python_version": "3.10",
            "idempotent": True,
        },
    }
    got = validate_policy(valid)
    if got:
        raise AssertionError(f"expected no errors, got: {got}")


def test_reject_duplicate_deprecation_ids() -> None:
    bad = {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "deprecations": [
            {
                "id": "dup",
                "since": "v1",
                "severity": "error",
                "replacement": "$",
                "autofix": True,
            },
            {
                "id": "dup",
                "since": "v1",
                "severity": "warning",
                "replacement": "x",
                "autofix": False,
            },
        ],
        "migration": {
            "tool": "scripts/evolution/migrate_to_v1.py",
            "min_python_version": "3.10",
            "idempotent": True,
        },
    }
    got = validate_policy(bad)
    if not any("duplicate deprecation id" in err for err in got):
        raise AssertionError(f"expected duplicate id error, got: {got}")


def test_reject_wrong_migration_tool() -> None:
    bad = {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "deprecations": [
            {
                "id": "class_sigil_section",
                "since": "v1",
                "severity": "error",
                "replacement": "$",
                "autofix": True,
            }
        ],
        "migration": {
            "tool": "scripts/evolution/other.py",
            "min_python_version": "3.10",
            "idempotent": True,
        },
    }
    got = validate_policy(bad)
    if not any("migration.tool" in err for err in got):
        raise AssertionError(f"expected migration.tool error, got: {got}")


def main() -> int:
    tests = [
        ("accept_valid_policy", test_accept_valid_policy),
        ("reject_duplicate_deprecation_ids", test_reject_duplicate_deprecation_ids),
        ("reject_wrong_migration_tool", test_reject_wrong_migration_tool),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"evolution policy regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
