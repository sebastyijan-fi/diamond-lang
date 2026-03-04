#!/usr/bin/env python3
"""Validate Diamond v1 memory/runtime and ABI/FFI policy contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = {
    "language",
    "profile_version",
    "status",
    "memory_runtime",
    "safety_boundary",
    "ffi_abi",
    "refs",
    "conformance",
}


def _read_text(path: Path, errors: list[str], label: str) -> str:
    if not path.is_file():
        errors.append(f"{label} missing path: {path}")
        return ""
    return path.read_text(encoding="utf-8")


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

    mem = policy.get("memory_runtime")
    safe = policy.get("safety_boundary")
    ffi = policy.get("ffi_abi")
    refs = policy.get("refs")
    conf = policy.get("conformance")
    if not isinstance(mem, dict):
        errors.append("memory_runtime must be an object")
        return errors
    if not isinstance(safe, dict):
        errors.append("safety_boundary must be an object")
        return errors
    if not isinstance(ffi, dict):
        errors.append("ffi_abi must be an object")
        return errors
    if not isinstance(refs, dict):
        errors.append("refs must be an object")
        return errors
    if not isinstance(conf, dict):
        errors.append("conformance must be an object")
        return errors

    if mem.get("python_model") != "gc":
        errors.append("memory_runtime.python_model must be 'gc'")
    if mem.get("js_model") != "gc":
        errors.append("memory_runtime.js_model must be 'gc'")
    if mem.get("rust_model") != "rc_refcell_compat":
        errors.append("memory_runtime.rust_model must be 'rc_refcell_compat'")
    if mem.get("manual_memory") is not False:
        errors.append("memory_runtime.manual_memory must be false")
    if mem.get("deterministic_destructor") is not False:
        errors.append("memory_runtime.deterministic_destructor must be false")

    if safe.get("unsafe_language_surface") != "none":
        errors.append("safety_boundary.unsafe_language_surface must be 'none'")
    if safe.get("rust_unsafe_blocks_allowed") is not False:
        errors.append("safety_boundary.rust_unsafe_blocks_allowed must be false")
    if safe.get("audit_mode") != "static_policy_gate":
        errors.append("safety_boundary.audit_mode must be 'static_policy_gate'")

    if ffi.get("c_abi_mode") != "host_extern_bridge":
        errors.append("ffi_abi.c_abi_mode must be 'host_extern_bridge'")
    if ffi.get("runtime_symbol") != "extern_call":
        errors.append("ffi_abi.runtime_symbol must be 'extern_call'")
    if ffi.get("default_behavior") != "not_implemented":
        errors.append("ffi_abi.default_behavior must be 'not_implemented'")

    required_refs = (
        "python_runtime",
        "rust_runtime",
        "rust_backend",
        "object_contract",
        "semantic_contract",
        "interop_policy",
        "conformance_cases",
    )
    for key in required_refs:
        ref = refs.get(key)
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"refs.{key} must be a non-empty string")
    if errors:
        return errors

    py_runtime = _read_text(repo_root / str(refs["python_runtime"]), errors, "refs.python_runtime")
    rs_runtime = _read_text(repo_root / str(refs["rust_runtime"]), errors, "refs.rust_runtime")
    rs_backend = _read_text(repo_root / str(refs["rust_backend"]), errors, "refs.rust_backend")
    obj_contract = _read_text(repo_root / str(refs["object_contract"]), errors, "refs.object_contract")
    sem_contract = _read_text(repo_root / str(refs["semantic_contract"]), errors, "refs.semantic_contract")
    interop_policy = _read_text(repo_root / str(refs["interop_policy"]), errors, "refs.interop_policy")
    cases_raw = _read_text(repo_root / str(refs["conformance_cases"]), errors, "refs.conformance_cases")

    for needle in ("def extern_call(",):
        if needle not in py_runtime:
            errors.append(f"refs.python_runtime missing symbol/token: {needle}")
    for needle in ("pub fn extern_call(", "panic::catch_unwind"):
        if needle not in rs_runtime:
            errors.append(f"refs.rust_runtime missing symbol/token: {needle}")
    if "unsafe " in rs_runtime or "unsafe{" in rs_runtime:
        errors.append("refs.rust_runtime contains disallowed unsafe block")
    if "catch_unwind" not in rs_backend:
        errors.append("refs.rust_backend missing panic boundary lowering (catch_unwind)")

    for needle in ("deterministic language-level destructors", "single-thread semantic domain", "non-`Send`"):
        if needle not in obj_contract:
            errors.append(f"refs.object_contract missing symbol/token: {needle}")
    for needle in ("Error Contract", "extern_call(symbol, args)", "single-thread domain"):
        if needle not in sem_contract:
            errors.append(f"refs.semantic_contract missing symbol/token: {needle}")
    for needle in ("C ABI interop", "extern", "extern_call"):
        if needle not in interop_policy:
            errors.append(f"refs.interop_policy missing symbol/token: {needle}")

    required_case_ids = conf.get("required_case_ids")
    if not isinstance(required_case_ids, list) or not required_case_ids:
        errors.append("conformance.required_case_ids must be a non-empty list")
        return errors
    if not all(isinstance(x, str) and x for x in required_case_ids):
        errors.append("conformance.required_case_ids must contain non-empty strings")
        return errors

    try:
        case_data = json.loads(cases_raw)
    except json.JSONDecodeError as exc:
        errors.append(f"refs.conformance_cases invalid json: {exc}")
        return errors

    found_ids: set[str] = set()
    _collect_ids(case_data, found_ids)
    for cid in required_case_ids:
        if cid not in found_ids:
            errors.append(f"conformance missing required case id: {cid}")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond memory/runtime policy.")
    ap.add_argument("--policy", required=True, help="Path to memory policy JSON")
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
        print(f"memory_policy: FAIL errors={len(errors)}")
        for err in errors:
            print(f"error: {err}")
        return 1

    print("memory_policy: OK profile=v1 checks=memory+safety+ffi_abi+lifecycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
