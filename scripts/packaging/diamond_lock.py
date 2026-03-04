#!/usr/bin/env python3
"""Generate deterministic Diamond lockfile for a source set."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _iter_inputs(in_path: Path) -> list[Path]:
    if in_path.is_file():
        return [in_path] if in_path.suffix == ".dmd" else []
    return sorted(p for p in in_path.glob("*.dmd") if p.is_file())


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _repo_rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_lock(inputs: list[Path], repo_root: Path) -> dict[str, object]:
    files = sorted(set(inputs))
    entries = [
        {
            "path": _repo_rel(fp, repo_root),
            "sha256": _sha256_file(fp),
            "bytes": fp.stat().st_size,
        }
        for fp in files
    ]
    digest = hashlib.sha256(
        "".join(f"{e['path']}:{e['sha256']}:{e['bytes']}\n" for e in entries).encode("utf-8")
    ).hexdigest()
    return {
        "language": "diamond",
        "lock_version": "1",
        "module_count": len(entries),
        "source_digest": digest,
        "modules": entries,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate deterministic Diamond lockfile.")
    ap.add_argument("--in", dest="inputs", action="append", required=True, help="Input .dmd path/dir")
    ap.add_argument("--out", required=True, help="Output lockfile path")
    ap.add_argument("--repo-root", default=".", help="Repo root for relative module paths")
    args = ap.parse_args()

    all_files: list[Path] = []
    for raw in args.inputs:
        all_files.extend(_iter_inputs(Path(raw)))
    all_files = sorted(set(all_files))
    if not all_files:
        print("diamond_lock: no .dmd files found")
        return 1

    lock = build_lock(all_files, Path(args.repo_root))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(lock, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        f"diamond_lock: wrote {out_path} modules={lock['module_count']} digest={lock['source_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
