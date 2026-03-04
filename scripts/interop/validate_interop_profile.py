#!/usr/bin/env python3
"""Validate Diamond v1 interop profile contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_TOP_LEVEL_KEYS = {
    "language",
    "profile_version",
    "status",
    "c_abi",
    "embedding",
    "wasm",
    "data_interchange",
}


def _read_text(path: Path, errors: list[str], label: str) -> str:
    if not path.is_file():
        errors.append(f"{label} missing path: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def _require_substrings(
    text: str,
    substrings: list[str],
    errors: list[str],
    label: str,
) -> None:
    for needle in substrings:
        if needle not in text:
            errors.append(f"{label} missing symbol/token: {needle}")


def validate_profile(profile: dict[str, object], repo_root: Path) -> list[str]:
    errors: list[str] = []

    for key in sorted(REQUIRED_TOP_LEVEL_KEYS):
        if key not in profile:
            errors.append(f"missing top-level key: {key}")
    if errors:
        return errors

    if profile.get("language") != "diamond":
        errors.append("language must be 'diamond'")
    if profile.get("profile_version") != "v1":
        errors.append("profile_version must be 'v1'")
    if profile.get("status") != "stable":
        errors.append("status must be 'stable'")

    c_abi = profile.get("c_abi")
    embedding = profile.get("embedding")
    wasm = profile.get("wasm")
    data = profile.get("data_interchange")
    if not isinstance(c_abi, dict):
        errors.append("c_abi must be an object")
        return errors
    if not isinstance(embedding, dict):
        errors.append("embedding must be an object")
        return errors
    if not isinstance(wasm, dict):
        errors.append("wasm must be an object")
        return errors
    if not isinstance(data, dict):
        errors.append("data_interchange must be an object")
        return errors

    if c_abi.get("extern_builtin") != "extern":
        errors.append("c_abi.extern_builtin must be 'extern'")
    if c_abi.get("runtime_symbol") != "extern_call":
        errors.append("c_abi.runtime_symbol must be 'extern_call'")

    py_runtime_ref = embedding.get("python_runtime")
    if not isinstance(py_runtime_ref, str) or not py_runtime_ref.strip():
        errors.append("embedding.python_runtime must be a non-empty string")
        return errors
    py_runtime_path = repo_root / py_runtime_ref
    py_runtime = _read_text(py_runtime_path, errors, "embedding.python_runtime")
    _require_substrings(
        py_runtime,
        ["def extern_call(", "def call_with(", "def json_dumps(", "def json_loads("],
        errors,
        "embedding.python_runtime",
    )

    wasm_js_runtime_ref = wasm.get("js_runtime")
    wasm_js_backend_ref = wasm.get("js_backend")
    if not isinstance(wasm_js_runtime_ref, str) or not wasm_js_runtime_ref.strip():
        errors.append("wasm.js_runtime must be a non-empty string")
        return errors
    if not isinstance(wasm_js_backend_ref, str) or not wasm_js_backend_ref.strip():
        errors.append("wasm.js_backend must be a non-empty string")
        return errors
    wasm_js_runtime = _read_text(repo_root / wasm_js_runtime_ref, errors, "wasm.js_runtime")
    wasm_js_backend = _read_text(repo_root / wasm_js_backend_ref, errors, "wasm.js_backend")
    _require_substrings(
        wasm_js_runtime,
        ["json_dumps", "json_loads"],
        errors,
        "wasm.js_runtime",
    )
    _require_substrings(
        wasm_js_backend,
        ["jenc", "jdec"],
        errors,
        "wasm.js_backend",
    )

    rust_runtime_ref = data.get("rust_runtime")
    py_backend_ref = data.get("python_backend")
    js_backend_ref = data.get("js_backend")
    rust_backend_ref = data.get("rust_backend")
    sem_ref = data.get("semantic_validator")
    for key, ref in (
        ("data_interchange.rust_runtime", rust_runtime_ref),
        ("data_interchange.python_backend", py_backend_ref),
        ("data_interchange.js_backend", js_backend_ref),
        ("data_interchange.rust_backend", rust_backend_ref),
        ("data_interchange.semantic_validator", sem_ref),
    ):
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"{key} must be a non-empty string")

    if errors:
        return errors

    rust_runtime = _read_text(repo_root / str(rust_runtime_ref), errors, "data_interchange.rust_runtime")
    py_backend = _read_text(repo_root / str(py_backend_ref), errors, "data_interchange.python_backend")
    js_backend = _read_text(repo_root / str(js_backend_ref), errors, "data_interchange.js_backend")
    rust_backend = _read_text(repo_root / str(rust_backend_ref), errors, "data_interchange.rust_backend")
    sem_validator = _read_text(repo_root / str(sem_ref), errors, "data_interchange.semantic_validator")

    _require_substrings(
        rust_runtime,
        ["json_dumps", "json_loads"],
        errors,
        "data_interchange.rust_runtime",
    )
    _require_substrings(py_backend, ["jenc", "jdec"], errors, "data_interchange.python_backend")
    _require_substrings(js_backend, ["jenc", "jdec"], errors, "data_interchange.js_backend")
    _require_substrings(rust_backend, ["jenc", "jdec"], errors, "data_interchange.rust_backend")
    _require_substrings(sem_validator, ["jenc", "jdec"], errors, "data_interchange.semantic_validator")

    if data.get("json_encode_builtin") != "jenc":
        errors.append("data_interchange.json_encode_builtin must be 'jenc'")
    if data.get("json_decode_builtin") != "jdec":
        errors.append("data_interchange.json_decode_builtin must be 'jdec'")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond interop profile JSON.")
    ap.add_argument("--profile", required=True, help="Path to interop profile JSON")
    ap.add_argument("--repo-root", default=".", help="Repository root for relative refs")
    args = ap.parse_args()

    profile_path = Path(args.profile)
    if not profile_path.is_file():
        print(f"error: profile file not found: {profile_path}")
        return 2

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid json: {exc}")
        return 2

    if not isinstance(profile, dict):
        print("error: profile root must be an object")
        return 2

    errors = validate_profile(profile, Path(args.repo_root))
    if errors:
        print(f"interop_profile: FAIL errors={len(errors)}")
        for err in errors:
            print(f"error: {err}")
        return 1

    print("interop_profile: OK profile=v1 checks=abi+embedding+wasm+data_interchange")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
