#!/usr/bin/env python3
"""Compatibility wrapper for the old Python-only stub command."""

from __future__ import annotations

import argparse

from transpile import main as transpile_main


def main() -> int:
    ap = argparse.ArgumentParser(description="Diamond -> Python stubs (compat wrapper)")
    ap.add_argument("--in", dest="in_path", required=True, help="Input .dmd file or directory")
    ap.add_argument("--out-dir", required=True, help="Output directory for generated .py files")
    ap.add_argument("--dump-ir-json", action="store_true", help="Also emit IR JSON for each module")
    args = ap.parse_args()

    argv = [
        "--in",
        args.in_path,
        "--backend",
        "python",
        "--out-dir",
        args.out_dir,
    ]
    if args.dump_ir_json:
        argv.append("--dump-ir-json")
    return transpile_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
