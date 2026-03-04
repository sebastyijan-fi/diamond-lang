#!/usr/bin/env python3
"""Diamond transpiler entrypoint with backend selection."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from backends import BACKENDS, get_backend
from capability_validate import validate_program_capabilities
from ir_json import to_jsonable
from parse_to_ir import build_parser, iter_inputs, parse_file
from semantic_validate import validate_program_semantics


def _ensure_runtime(out_dir: Path, backend: str) -> None:
    src_dir = Path(__file__).resolve().parent / "runtime"
    suffix = {
        "python": "py",
        "js": "js",
        "rust": "rs",
        "wasm": "js",
    }[backend]
    src = src_dir / f"diamond_runtime.{suffix}"
    dst = out_dir / f"diamond_runtime.{suffix}"
    shutil.copyfile(src, dst)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Diamond transpiler (shared parser/IR, pluggable backends)")
    ap.add_argument("--in", dest="in_path", required=True, help="Input .dmd file or directory")
    ap.add_argument("--backend", required=True, choices=sorted(BACKENDS.keys()))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--dump-ir-json", action="store_true", help="Write <stem>.ir.json next to emitted file")
    ap.add_argument(
        "--skip-capability-validation",
        action="store_true",
        help="Skip static capability composition validation pass",
    )
    ap.add_argument(
        "--skip-semantic-validation",
        action="store_true",
        help="Skip static semantic/type validation pass",
    )
    args = ap.parse_args(argv)

    in_path = Path(args.in_path)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.backend in {"python", "js", "rust", "wasm"}:
        _ensure_runtime(out_dir, args.backend)

    ext, emitter = get_backend(args.backend)
    parser = build_parser()

    inputs = iter_inputs(in_path)
    if not inputs:
        print("no input .dmd files found")
        return 1

    count = 0
    for dm in inputs:
        program = parse_file(dm, parser=parser)
        if not args.skip_semantic_validation:
            sem_report = validate_program_semantics(program)
            if sem_report.errors:
                details = "\n".join(f"  - {msg}" for msg in sem_report.errors)
                raise ValueError(
                    f"semantic validation failed for {dm} ({program.module_name}):\n{details}"
                )
        if not args.skip_capability_validation:
            report = validate_program_capabilities(program)
            if report.errors:
                details = "\n".join(f"  - {msg}" for msg in report.errors)
                raise ValueError(
                    f"capability validation failed for {dm} ({program.module_name}):\n{details}"
                )
        target = out_dir / (dm.stem + ext)
        target.write_text(emitter(program), encoding="utf-8")
        print(f"wrote {target}")

        if args.dump_ir_json:
            ir_path = out_dir / (dm.stem + ".ir.json")
            ir_path.write_text(json.dumps(to_jsonable(program), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            print(f"wrote {ir_path}")

        count += 1

    print(f"generated {count} files via backend={args.backend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
