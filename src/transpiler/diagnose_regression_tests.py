#!/usr/bin/env python3
"""Regression tests for dm diagnose JSON schema and core parse diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from diagnose import SCHEMA_VERSION, run


BAD_DIR = Path("src/transpiler/testdata/diagnose_bad")


def _load_file_entry(report: dict, suffix: str) -> dict:
    for item in report["files"]:
        if item["file"].endswith(suffix):
            return item
    raise AssertionError(f"missing report entry for {suffix}")


def test_bad_samples() -> None:
    report = run(BAD_DIR)
    if report["schema_version"] != SCHEMA_VERSION:
        raise AssertionError("schema_version mismatch")
    if report["ok"]:
        raise AssertionError("expected failing report for malformed samples")
    if report["error_count"] < 3:
        raise AssertionError(f"expected >=3 errors, got {report['error_count']}")

    f1 = _load_file_entry(report, "01_missing_expr.dmd")
    d1 = f1["diagnostics"][0]
    if d1["code"] != "DM_PARSE_UNEXPECTED_TOKEN":
        raise AssertionError("missing_expr should be unexpected token")
    if d1["got_token"] != "$END":
        raise AssertionError("missing_expr should report got_token=$END")
    if not d1["expected_tokens"]:
        raise AssertionError("missing_expr expected_tokens must be non-empty")

    f2 = _load_file_entry(report, "02_unexpected_char.dmd")
    d2 = f2["diagnostics"][0]
    if d2["code"] == "DM_PARSE_UNEXPECTED_CHAR":
        if d2["got_token"] != "@":
            raise AssertionError("unexpected_char should report '@'")
    elif d2["code"] == "DM_PARSE_UNEXPECTED_TOKEN":
        if d2["got_token"] != "AT":
            raise AssertionError("unexpected_char token form should report got_token=AT")
    else:
        raise AssertionError("unexpected_char should be unexpected character/token-at")

    f3 = _load_file_entry(report, "03_ternary_missing_colon.dmd")
    d3 = f3["diagnostics"][0]
    if d3["code"] != "DM_PARSE_UNEXPECTED_TOKEN":
        raise AssertionError("ternary_missing_colon should be unexpected token")
    if "COLON" not in d3["expected_tokens"]:
        raise AssertionError("ternary_missing_colon should expect COLON")


def test_good_sample() -> None:
    report = run(Path("docs/decisions/profile_v1/programs/01_fizzbuzz.dmd"))
    if not report["ok"]:
        raise AssertionError("valid sample should pass diagnostics")
    if report["error_count"] != 0:
        raise AssertionError("valid sample should have zero errors")


def main() -> int:
    tests = [
        ("bad_samples", test_bad_samples),
        ("good_sample", test_good_sample),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"diagnose regressions: {len(tests)}/{len(tests)} passing")
    # emit one compact schema example for visibility in logs
    sample = run(BAD_DIR)
    print("schema_preview:", json.dumps({"schema_version": sample["schema_version"], "keys": sorted(sample.keys())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
