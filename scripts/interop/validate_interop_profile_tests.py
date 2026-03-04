#!/usr/bin/env python3
"""Regression tests for interop profile validator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from validate_interop_profile import validate_profile


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_profile() -> dict[str, object]:
    return {
        "language": "diamond",
        "profile_version": "v1",
        "status": "stable",
        "c_abi": {
            "extern_builtin": "extern",
            "runtime_symbol": "extern_call",
        },
        "embedding": {
            "python_runtime": "runtime/diamond_runtime.py",
        },
        "wasm": {
            "js_runtime": "runtime/diamond_runtime.js",
            "js_backend": "backends/js_backend.py",
        },
        "data_interchange": {
            "rust_runtime": "runtime/diamond_runtime.rs",
            "python_backend": "backends/python_backend.py",
            "js_backend": "backends/js_backend.py",
            "rust_backend": "backends/rust_backend.py",
            "semantic_validator": "semantic_validate.py",
            "json_encode_builtin": "jenc",
            "json_decode_builtin": "jdec",
        },
    }


def _seed_valid_tree(root: Path) -> None:
    _write(
        root / "runtime/diamond_runtime.py",
        "def extern_call():\n    pass\ndef call_with():\n    pass\ndef json_dumps():\n    pass\ndef json_loads():\n    pass\n",
    )
    _write(root / "runtime/diamond_runtime.js", "function json_dumps(){}\nfunction json_loads(){}\n")
    _write(root / "runtime/diamond_runtime.rs", "pub fn json_dumps(){}\npub fn json_loads(){}\n")
    _write(root / "backends/python_backend.py", "BUILTINS={'jenc':'x','jdec':'y'}\n")
    _write(root / "backends/js_backend.py", "BUILTINS={'jenc':'x','jdec':'y'}\n")
    _write(root / "backends/rust_backend.py", "BUILTINS={'jenc':'x','jdec':'y'}\n")
    _write(root / "semantic_validate.py", "SIG={'jenc':1,'jdec':1}\n")


def test_accept_valid_profile() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_valid_tree(root)
        errors = validate_profile(_valid_profile(), root)
        if errors:
            raise AssertionError(f"expected no errors, got: {errors}")


def test_reject_missing_runtime_symbol() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_valid_tree(root)
        (root / "runtime/diamond_runtime.py").write_text(
            "def call_with():\n    pass\ndef json_dumps():\n    pass\ndef json_loads():\n    pass\n",
            encoding="utf-8",
        )
        errors = validate_profile(_valid_profile(), root)
        if not any("extern_call" in err for err in errors):
            raise AssertionError(f"expected extern_call error, got: {errors}")


def test_reject_wrong_builtin_contract() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_valid_tree(root)
        profile = _valid_profile()
        data = profile["data_interchange"]
        if not isinstance(data, dict):
            raise AssertionError("invalid test profile")
        data["json_encode_builtin"] = "json"
        errors = validate_profile(profile, root)
        if not any("json_encode_builtin" in err for err in errors):
            raise AssertionError(f"expected builtin contract error, got: {errors}")


def main() -> int:
    tests = [
        ("accept_valid_profile", test_accept_valid_profile),
        ("reject_missing_runtime_symbol", test_reject_missing_runtime_symbol),
        ("reject_wrong_builtin_contract", test_reject_wrong_builtin_contract),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"interop profile regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
