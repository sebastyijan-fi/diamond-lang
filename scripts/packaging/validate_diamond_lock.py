#!/usr/bin/env python3
"""Validate deterministic Diamond lockfile against source set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from diamond_lock import build_lock


def _iter_inputs(in_path: Path) -> list[Path]:
    if in_path.is_file():
        return [in_path] if in_path.suffix == ".dmd" else []
    return sorted(p for p in in_path.glob("*.dmd") if p.is_file())


def validate_lock(
    lock_path: Path,
    inputs: list[Path],
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    if not lock_path.is_file():
        return [f"missing lockfile: {lock_path}"]

    try:
        on_disk = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid lock json: {exc}"]

    if not isinstance(on_disk, dict):
        return ["lock root must be object"]

    expected = build_lock(inputs, repo_root)

    for key in ("language", "lock_version", "module_count", "source_digest", "modules"):
        if key not in on_disk:
            errors.append(f"missing key: {key}")

    if on_disk.get("language") != "diamond":
        errors.append("language must be 'diamond'")
    if on_disk.get("lock_version") != "1":
        errors.append("lock_version must be '1'")

    if on_disk.get("module_count") != expected["module_count"]:
        errors.append(
            f"module_count mismatch: lock={on_disk.get('module_count')} expected={expected['module_count']}"
        )
    if on_disk.get("source_digest") != expected["source_digest"]:
        errors.append(
            f"source_digest mismatch: lock={on_disk.get('source_digest')} expected={expected['source_digest']}"
        )

    lock_modules = on_disk.get("modules")
    if not isinstance(lock_modules, list):
        errors.append("modules must be a list")
        return errors
    if lock_modules != expected["modules"]:
        errors.append("modules entries mismatch expected deterministic ordering/checksums")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond lockfile determinism.")
    ap.add_argument("--lock", required=True, help="Path to diamond.lock.json")
    ap.add_argument("--in", dest="inputs", action="append", required=True, help="Input .dmd path/dir")
    ap.add_argument("--repo-root", default=".", help="Repo root for relative module paths")
    args = ap.parse_args()

    files: list[Path] = []
    for raw in args.inputs:
        files.extend(_iter_inputs(Path(raw)))
    files = sorted(set(files))
    if not files:
        print("validate_diamond_lock: no .dmd files found")
        return 1

    errors = validate_lock(Path(args.lock), files, Path(args.repo_root))
    if errors:
        print(f"validate_diamond_lock: FAIL errors={len(errors)}")
        for err in errors:
            print(f"error: {err}")
        return 1

    print(f"validate_diamond_lock: OK lock={args.lock} modules={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
