#!/usr/bin/env python3
"""Validate Diamond v1 panic/cleanup policy contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = {
    "language",
    "profile_version",
    "status",
    "panic_cleanup",
    "runtime_refs",
    "conformance",
}


def _collect_ids(node: Any, out: set[str]) -> None:
    if isinstance(node, dict):
        value = node.get("id")
        if isinstance(value, str) and value:
            out.add(value)
        for v in node.values():
            _collect_ids(v, out)
        return
    if isinstance(node, list):
        for v in node:
            _collect_ids(v, out)


def _read_text(path: Path, errors: list[str], label: str) -> str:
    if not path.is_file():
        errors.append(f"{label} missing path: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def validate_policy(policy: dict[str, object], repo_root: Path) -> list[str]:
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

    panic_cleanup = policy.get("panic_cleanup")
    runtime_refs = policy.get("runtime_refs")
    conformance = policy.get("conformance")
    if not isinstance(panic_cleanup, dict):
        errors.append("panic_cleanup must be an object")
        return errors
    if not isinstance(runtime_refs, dict):
        errors.append("runtime_refs must be an object")
        return errors
    if not isinstance(conformance, dict):
        errors.append("conformance must be an object")
        return errors

    if panic_cleanup.get("panic_mode") != "exception_channel":
        errors.append("panic_cleanup.panic_mode must be 'exception_channel'")
    if panic_cleanup.get("cleanup_model") != "try_catch_handler":
        errors.append("panic_cleanup.cleanup_model must be 'try_catch_handler'")
    if panic_cleanup.get("reraise_sentinel") != "RERAISE":
        errors.append("panic_cleanup.reraise_sentinel must be 'RERAISE'")

    py_runtime_ref = runtime_refs.get("python_runtime")
    sem_contract_ref = runtime_refs.get("semantic_contract")
    for key, ref in (
        ("runtime_refs.python_runtime", py_runtime_ref),
        ("runtime_refs.semantic_contract", sem_contract_ref),
    ):
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"{key} must be a non-empty string")

    if errors:
        return errors

    py_runtime = _read_text(repo_root / str(py_runtime_ref), errors, "runtime_refs.python_runtime")
    sem_contract = _read_text(repo_root / str(sem_contract_ref), errors, "runtime_refs.semantic_contract")

    for needle in ("RERAISE", "def try_catch(", "def propagate("):
        if needle not in py_runtime:
            errors.append(f"runtime_refs.python_runtime missing symbol/token: {needle}")
    for needle in ("## 4) Error Contract", "try(body, e: handler)", "reraise"):
        if needle not in sem_contract:
            errors.append(f"runtime_refs.semantic_contract missing symbol/token: {needle}")

    cases_ref = conformance.get("cases_file")
    required_ids = conformance.get("required_case_ids")
    if not isinstance(cases_ref, str) or not cases_ref.strip():
        errors.append("conformance.cases_file must be a non-empty string")
        return errors
    if not isinstance(required_ids, list) or not required_ids:
        errors.append("conformance.required_case_ids must be a non-empty list")
        return errors
    if not all(isinstance(x, str) and x for x in required_ids):
        errors.append("conformance.required_case_ids must contain non-empty strings")
        return errors

    case_path = repo_root / cases_ref
    if not case_path.is_file():
        errors.append(f"conformance.cases_file missing path: {case_path}")
        return errors
    try:
        data = json.loads(case_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"conformance.cases_file invalid json: {exc}")
        return errors

    found_ids: set[str] = set()
    _collect_ids(data, found_ids)
    for cid in required_ids:
        if cid not in found_ids:
            errors.append(f"conformance missing required case id: {cid}")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond panic/cleanup policy.")
    ap.add_argument("--policy", required=True, help="Path to policy JSON")
    ap.add_argument("--repo-root", default=".", help="Repository root for relative refs")
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

    errors = validate_policy(policy, Path(args.repo_root))
    if errors:
        print(f"panic_policy: FAIL errors={len(errors)}")
        for err in errors:
            print(f"error: {err}")
        return 1

    print("panic_policy: OK profile=v1 checks=panic+cleanup+reraise+conformance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
