#!/usr/bin/env python3
"""Differential case-by-case parity check for tomli upstream vs transpiled package.

This script compares behavior on every TOML file under upstream tests/data:
- valid/**/*.toml: both must parse and produce equal Python values
- invalid/**/*.toml: both must fail with TOMLDecodeError

It exits non-zero on any mismatch.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


def _load_pkg(alias: str, init_py: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        alias,
        str(init_py),
        submodule_search_locations=[str(init_py.parent)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed loading package spec: {init_py}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


def _read_toml_utf8(path: Path) -> tuple[str | None, str | None]:
    raw = path.read_bytes()
    try:
        return raw.decode(), None
    except UnicodeDecodeError as exc:
        return None, str(exc)


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _deep_equal(a: Any, b: Any) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_deep_equal(a[k], b[k]) for k in a.keys())
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_deep_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, tuple) and isinstance(b, tuple):
        if len(a) != len(b):
            return False
        return all(_deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--upstream-init",
        default="certification/real-repos/tomli/upstream/tomli/src/tomli/__init__.py",
    )
    parser.add_argument(
        "--transpiled-init",
        default="certification/real-repos/tomli/out/pkg/tomli/__init__.py",
    )
    parser.add_argument(
        "--data-dir",
        default="certification/real-repos/tomli/upstream/tomli/tests/data",
    )
    parser.add_argument(
        "--report-json",
        default="certification/real-repos/tomli/out/diff_report.json",
    )
    args = parser.parse_args()

    upstream_init = Path(args.upstream_init)
    transpiled_init = Path(args.transpiled_init)
    data_dir = Path(args.data_dir)
    report_json = Path(args.report_json)

    if not upstream_init.is_file():
        raise FileNotFoundError(f"upstream init missing: {upstream_init}")
    if not transpiled_init.is_file():
        raise FileNotFoundError(f"transpiled init missing: {transpiled_init}")
    if not data_dir.is_dir():
        raise FileNotFoundError(f"data dir missing: {data_dir}")

    # Transpiled package expects sibling module diamond_runtime at pkg root.
    transpiled_pkg_root = transpiled_init.parent.parent
    if str(transpiled_pkg_root) not in sys.path:
        sys.path.insert(0, str(transpiled_pkg_root))

    tomli_up = _load_pkg("tomli_up", upstream_init)
    tomli_dm = _load_pkg("tomli_dm", transpiled_init)

    valid_files = sorted((data_dir / "valid").glob("**/*.toml"))
    invalid_files = sorted((data_dir / "invalid").glob("**/*.toml"))

    valid_ok = 0
    invalid_ok = 0
    skipped_non_utf8 = 0
    mismatches: list[dict[str, Any]] = []
    invalid_msg_match = 0

    for path in valid_files:
        toml_str, decode_err = _read_toml_utf8(path)
        if decode_err is not None:
            skipped_non_utf8 += 1
            continue

        assert toml_str is not None
        rel = _rel(path, data_dir)
        try:
            up_v = tomli_up.loads(toml_str)
        except Exception as exc:  # pragma: no cover - explicit reporting path
            mismatches.append(
                {
                    "kind": "valid",
                    "file": rel,
                    "reason": "upstream_raised",
                    "upstream_exc": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        try:
            dm_v = tomli_dm.loads(toml_str)
        except Exception as exc:
            mismatches.append(
                {
                    "kind": "valid",
                    "file": rel,
                    "reason": "transpiled_raised",
                    "transpiled_exc": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        if not _deep_equal(up_v, dm_v):
            mismatches.append(
                {
                    "kind": "valid",
                    "file": rel,
                    "reason": "value_mismatch",
                    "upstream_repr": repr(up_v),
                    "transpiled_repr": repr(dm_v),
                }
            )
            continue

        valid_ok += 1

    for path in invalid_files:
        toml_str, decode_err = _read_toml_utf8(path)
        if decode_err is not None:
            skipped_non_utf8 += 1
            continue

        assert toml_str is not None
        rel = _rel(path, data_dir)

        up_exc: BaseException | None = None
        dm_exc: BaseException | None = None
        try:
            tomli_up.loads(toml_str)
        except Exception as exc:
            up_exc = exc
        try:
            tomli_dm.loads(toml_str)
        except Exception as exc:
            dm_exc = exc

        if up_exc is None:
            mismatches.append(
                {"kind": "invalid", "file": rel, "reason": "upstream_accepted_invalid"}
            )
            continue
        if dm_exc is None:
            mismatches.append(
                {"kind": "invalid", "file": rel, "reason": "transpiled_accepted_invalid"}
            )
            continue

        if not isinstance(up_exc, tomli_up.TOMLDecodeError):
            mismatches.append(
                {
                    "kind": "invalid",
                    "file": rel,
                    "reason": "upstream_wrong_exc_type",
                    "exc_type": type(up_exc).__name__,
                }
            )
            continue
        if not isinstance(dm_exc, tomli_dm.TOMLDecodeError):
            mismatches.append(
                {
                    "kind": "invalid",
                    "file": rel,
                    "reason": "transpiled_wrong_exc_type",
                    "exc_type": type(dm_exc).__name__,
                }
            )
            continue

        if str(up_exc) == str(dm_exc):
            invalid_msg_match += 1
        invalid_ok += 1

    total_cases = len(valid_files) + len(invalid_files)
    executed_cases = valid_ok + invalid_ok + len(mismatches)

    summary = {
        "total_cases": total_cases,
        "executed_cases": executed_cases,
        "valid_cases": len(valid_files),
        "invalid_cases": len(invalid_files),
        "valid_ok": valid_ok,
        "invalid_ok": invalid_ok,
        "invalid_message_exact_match": invalid_msg_match,
        "skipped_non_utf8": skipped_non_utf8,
        "mismatch_count": len(mismatches),
    }

    report = {"summary": summary, "mismatches": mismatches}
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("[diff] summary")
    print(json.dumps(summary, indent=2))
    print(f"[diff] report: {report_json}")

    if mismatches:
        print("[diff] FAIL: mismatches detected")
        return 1
    print("[diff] PASS: full case parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
