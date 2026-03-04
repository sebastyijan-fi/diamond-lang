#!/usr/bin/env python3
"""Validate Diamond v1 evolution policy document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_TOP_LEVEL_KEYS = {
    "language",
    "profile_version",
    "status",
    "deprecations",
    "migration",
}

REQUIRED_DEPRECATION_KEYS = {
    "id",
    "since",
    "severity",
    "replacement",
    "autofix",
}


def validate_policy(policy: dict[str, object]) -> list[str]:
    errors: list[str] = []

    for key in sorted(REQUIRED_TOP_LEVEL_KEYS):
        if key not in policy:
            errors.append(f"missing top-level key: {key}")

    if errors:
        return errors

    if policy.get("language") != "diamond":
        errors.append("language must be 'diamond'")

    if policy.get("profile_version") != "v1":
        errors.append("profile_version must be 'v1'")

    if policy.get("status") != "stable":
        errors.append("status must be 'stable'")

    deprecations = policy.get("deprecations")
    if not isinstance(deprecations, list) or not deprecations:
        errors.append("deprecations must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for idx, raw in enumerate(deprecations):
        if not isinstance(raw, dict):
            errors.append(f"deprecations[{idx}] must be an object")
            continue

        for key in sorted(REQUIRED_DEPRECATION_KEYS):
            if key not in raw:
                errors.append(f"deprecations[{idx}] missing key: {key}")

        dep_id = raw.get("id")
        if isinstance(dep_id, str):
            if dep_id in seen_ids:
                errors.append(f"duplicate deprecation id: {dep_id}")
            seen_ids.add(dep_id)
        else:
            errors.append(f"deprecations[{idx}].id must be a string")

        if raw.get("since") != "v1":
            errors.append(f"deprecations[{idx}].since must be 'v1'")

        severity = raw.get("severity")
        if severity not in {"error", "warning"}:
            errors.append(f"deprecations[{idx}].severity must be error|warning")

        replacement = raw.get("replacement")
        if not isinstance(replacement, str) or not replacement.strip():
            errors.append(f"deprecations[{idx}].replacement must be a non-empty string")

        autofix = raw.get("autofix")
        if not isinstance(autofix, bool):
            errors.append(f"deprecations[{idx}].autofix must be a bool")

    migration = policy.get("migration")
    if not isinstance(migration, dict):
        errors.append("migration must be an object")
        return errors

    for key in ("tool", "min_python_version", "idempotent"):
        if key not in migration:
            errors.append(f"migration missing key: {key}")

    if migration.get("tool") != "scripts/evolution/migrate_to_v1.py":
        errors.append("migration.tool must reference scripts/evolution/migrate_to_v1.py")

    min_py = migration.get("min_python_version")
    if not isinstance(min_py, str) or not min_py.strip():
        errors.append("migration.min_python_version must be a non-empty string")

    idem = migration.get("idempotent")
    if idem is not True:
        errors.append("migration.idempotent must be true")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond evolution policy JSON.")
    ap.add_argument("--policy", required=True, help="Path to policy JSON file")
    args = ap.parse_args()

    policy_path = Path(args.policy)
    if not policy_path.is_file():
        print(f"error: policy file not found: {policy_path}")
        return 2

    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid json: {exc}")
        return 2

    if not isinstance(policy, dict):
        print("error: policy root must be an object")
        return 2

    errors = validate_policy(policy)
    if errors:
        print(f"evolution_policy: FAIL errors={len(errors)}")
        for err in errors:
            print(f"error: {err}")
        return 1

    deprecations = policy["deprecations"]
    print(
        "evolution_policy: OK "
        f"profile={policy['profile_version']} status={policy['status']} deprecations={len(deprecations)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
