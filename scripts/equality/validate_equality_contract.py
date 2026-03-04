#!/usr/bin/env python3
"""Validate Diamond v1 equality/identity/hash contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = {
    "language",
    "profile_version",
    "status",
    "equality",
    "identity",
    "hash",
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


def validate_contract(contract: dict[str, object], repo_root: Path) -> list[str]:
    errors: list[str] = []

    for key in sorted(REQUIRED_TOP_LEVEL_KEYS):
        if key not in contract:
            errors.append(f"missing top-level key: {key}")
    if errors:
        return errors

    if contract.get("language") != "diamond":
        errors.append("language must be 'diamond'")
    if contract.get("profile_version") != "v1":
        errors.append("profile_version must be 'v1'")
    if contract.get("status") != "stable":
        errors.append("status must be 'stable'")

    eq = contract.get("equality")
    ident = contract.get("identity")
    hsh = contract.get("hash")
    runtime_refs = contract.get("runtime_refs")
    conf = contract.get("conformance")
    if not isinstance(eq, dict):
        errors.append("equality must be an object")
        return errors
    if not isinstance(ident, dict):
        errors.append("identity must be an object")
        return errors
    if not isinstance(hsh, dict):
        errors.append("hash must be an object")
        return errors
    if not isinstance(runtime_refs, dict):
        errors.append("runtime_refs must be an object")
        return errors
    if not isinstance(conf, dict):
        errors.append("conformance must be an object")
        return errors

    if eq.get("mode") != "structural_deep_cycle_safe":
        errors.append("equality.mode must be 'structural_deep_cycle_safe'")
    if ident.get("mode") != "reference":
        errors.append("identity.mode must be 'reference'")
    if hsh.get("objects") != "unhashable":
        errors.append("hash.objects must be 'unhashable'")
    if hsh.get("scalars_stable") is not True:
        errors.append("hash.scalars_stable must be true")

    py_runtime_ref = runtime_refs.get("python")
    js_runtime_ref = runtime_refs.get("js")
    for key, ref in (("runtime_refs.python", py_runtime_ref), ("runtime_refs.js", js_runtime_ref)):
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"{key} must be a non-empty string")
    if errors:
        return errors

    py_runtime = _read_text(repo_root / str(py_runtime_ref), errors, "runtime_refs.python")
    js_runtime = _read_text(repo_root / str(js_runtime_ref), errors, "runtime_refs.js")
    if "def obj_is(" not in py_runtime:
        errors.append("runtime_refs.python missing obj_is implementation")
    if "def obj_eq(" not in py_runtime:
        errors.append("runtime_refs.python missing obj_eq implementation")
    if "export function obj_is" not in js_runtime:
        errors.append("runtime_refs.js missing obj_is implementation")
    if "export function obj_eq" not in js_runtime:
        errors.append("runtime_refs.js missing obj_eq implementation")

    case_file_ref = conf.get("cases_file")
    required_ids = conf.get("required_case_ids")
    if not isinstance(case_file_ref, str) or not case_file_ref.strip():
        errors.append("conformance.cases_file must be a non-empty string")
        return errors
    if not isinstance(required_ids, list) or not required_ids:
        errors.append("conformance.required_case_ids must be a non-empty list")
        return errors
    if not all(isinstance(x, str) and x for x in required_ids):
        errors.append("conformance.required_case_ids must contain non-empty strings")
        return errors

    case_path = repo_root / case_file_ref
    if not case_path.is_file():
        errors.append(f"conformance.cases_file missing path: {case_path}")
        return errors
    try:
        case_data = json.loads(case_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"conformance.cases_file invalid json: {exc}")
        return errors

    found_ids: set[str] = set()
    _collect_ids(case_data, found_ids)
    for cid in required_ids:
        if cid not in found_ids:
            errors.append(f"conformance missing required case id: {cid}")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond equality/identity/hash contract JSON.")
    ap.add_argument("--contract", required=True, help="Path to contract JSON")
    ap.add_argument("--repo-root", default=".", help="Repository root for relative refs")
    args = ap.parse_args()

    contract_path = Path(args.contract)
    if not contract_path.is_file():
        print(f"error: contract file not found: {contract_path}")
        return 2

    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid json: {exc}")
        return 2

    if not isinstance(contract, dict):
        print("error: contract root must be an object")
        return 2

    errors = validate_contract(contract, Path(args.repo_root))
    if errors:
        print(f"equality_contract: FAIL errors={len(errors)}")
        for err in errors:
            print(f"error: {err}")
        return 1

    print("equality_contract: OK profile=v1 checks=equality+identity+hash+conformance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
