#!/usr/bin/env python3
"""Measure Diamond construct-tool budget vs Python baselines.

Computes per-program and aggregate metrics:
- syntax_reduction = (python_tokens - diamond_base_tokens) / python_tokens
- tool_overhead = (diamond_full_tokens - diamond_base_tokens) / diamond_base_tokens
- net_reduction = (python_tokens - diamond_full_tokens) / python_tokens
- vs_python_with_tools = (python_with_tools_tokens - diamond_full_tokens) / python_with_tools_tokens
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Row:
    program: str
    py: int
    py_tools: int
    dm_base: int
    dm_full: int


def list_files(base: pathlib.Path, pattern: str) -> dict[str, pathlib.Path]:
    out: dict[str, pathlib.Path] = {}
    for p in sorted(base.glob(pattern)):
        out[p.stem] = p
    return out


def count_with_cmd(path: pathlib.Path, cmd_template: str) -> int:
    if "{file}" not in cmd_template:
        raise SystemExit("--tokenizer-cmd must include {file} placeholder")
    cmd = cmd_template.replace("{file}", shlex.quote(str(path)))
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"Tokenizer command failed for {path.name}:\n{proc.stderr.strip()}")
    m = re.search(r"(\d+)", proc.stdout.strip())
    if not m:
        raise SystemExit(f"Tokenizer command did not output integer for {path.name}")
    return int(m.group(1))


def count_with_hf(path: pathlib.Path, tokenizer_path: str) -> int:
    from transformers import AutoTokenizer  # type: ignore

    tok = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    txt = path.read_text(encoding="utf-8")
    return len(tok.encode(txt, add_special_tokens=False))


def count_with_tokenizer_json(path: pathlib.Path, tokenizer_json: str) -> int:
    from tokenizers import Tokenizer  # type: ignore

    tok = Tokenizer.from_file(tokenizer_json)
    txt = path.read_text(encoding="utf-8")
    return len(tok.encode(txt).ids)


def count_with_heuristic(path: pathlib.Path) -> int:
    txt = path.read_text(encoding="utf-8")
    return len(re.findall(r"[A-Za-z_][A-Za-z_0-9]*|\d+\.\d+|\d+|\S", txt))


def count_tokens(path: pathlib.Path, args: argparse.Namespace) -> int:
    if args.tokenizer_json:
        return count_with_tokenizer_json(path, args.tokenizer_json)
    if args.hf_tokenizer_path:
        return count_with_hf(path, args.hf_tokenizer_path)
    if args.tokenizer_cmd:
        return count_with_cmd(path, args.tokenizer_cmd)
    if args.heuristic:
        return count_with_heuristic(path)
    raise SystemExit("Choose one backend: --tokenizer-json, --hf-tokenizer-path, --tokenizer-cmd, or --heuristic")


def pct(a: int, b: int) -> float:
    if b == 0:
        return 0.0
    return a / b


def tokenizer_meta(args: argparse.Namespace) -> tuple[str, str]:
    if args.tokenizer_json:
        return "tokenizer_json", args.tokenizer_json
    if args.hf_tokenizer_path:
        return "hf", args.hf_tokenizer_path
    if args.tokenizer_cmd:
        return "cmd", args.tokenizer_cmd
    return "heuristic", "regex_proxy"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_rows(args: argparse.Namespace) -> list[Row]:
    py = list_files(pathlib.Path(args.python_dir), args.python_pattern)
    py_tools = list_files(pathlib.Path(args.python_tools_dir), args.python_tools_pattern)
    dm_base = list_files(pathlib.Path(args.diamond_base_dir), args.diamond_base_pattern)
    dm_full = list_files(pathlib.Path(args.diamond_full_dir), args.diamond_full_pattern)

    all_keys = sorted(set(py) | set(py_tools) | set(dm_base) | set(dm_full))
    keys = sorted(set(py) & set(py_tools) & set(dm_base) & set(dm_full))
    if not keys:
        raise SystemExit("No shared program stems across all four inputs")

    missing = []
    for k in all_keys:
        miss = []
        if k not in py:
            miss.append("python")
        if k not in py_tools:
            miss.append("python_with_tools")
        if k not in dm_base:
            miss.append("diamond_base")
        if k not in dm_full:
            miss.append("diamond_full")
        if miss:
            missing.append((k, miss))
    if missing:
        print("warning: dropping stems missing in one or more inputs:")
        for stem, miss in missing:
            print(f"  {stem}: missing {','.join(miss)}")

    rows: list[Row] = []
    for k in keys:
        rows.append(
            Row(
                program=k,
                py=count_tokens(py[k], args),
                py_tools=count_tokens(py_tools[k], args),
                dm_base=count_tokens(dm_base[k], args),
                dm_full=count_tokens(dm_full[k], args),
            )
        )
    return rows


def write_jsonl(args: argparse.Namespace, rows: list[Row]) -> None:
    if not args.append_jsonl:
        return

    path = pathlib.Path(args.append_jsonl)
    path.parent.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    backend, ref = tokenizer_meta(args)

    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            rec = {
                "record_type": "construct_tool_measurement",
                "ts_utc": utc_now_iso(),
                "run_id": run_id,
                "question": args.question,
                "candidate": args.candidate,
                "program": r.program,
                "python_tokens": r.py,
                "python_with_tools": r.py_tools,
                "diamond_base": r.dm_base,
                "diamond_full": r.dm_full,
                "syntax_reduction": pct(r.py - r.dm_base, r.py),
                "tool_overhead": pct(r.dm_full - r.dm_base, r.dm_base),
                "net_reduction": pct(r.py - r.dm_full, r.py),
                "vs_python_with_tools": pct(r.py_tools - r.dm_full, r.py_tools),
                "tokenizer_backend": backend,
                "tokenizer_ref": ref,
                "notes": args.notes,
            }
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")

        py_total = sum(r.py for r in rows)
        pyt_total = sum(r.py_tools for r in rows)
        dmb_total = sum(r.dm_base for r in rows)
        dmf_total = sum(r.dm_full for r in rows)

        summary = {
            "record_type": "construct_tool_summary",
            "ts_utc": utc_now_iso(),
            "run_id": run_id,
            "question": args.question,
            "candidate": args.candidate,
            "files_measured": len(rows),
            "python_total": py_total,
            "python_with_tools_total": pyt_total,
            "diamond_base_total": dmb_total,
            "diamond_full_total": dmf_total,
            "syntax_reduction": pct(py_total - dmb_total, py_total),
            "tool_overhead": pct(dmf_total - dmb_total, dmb_total),
            "net_reduction": pct(py_total - dmf_total, py_total),
            "vs_python_with_tools": pct(pyt_total - dmf_total, pyt_total),
            "tokenizer_backend": backend,
            "tokenizer_ref": ref,
            "notes": args.notes,
        }
        f.write(json.dumps(summary, ensure_ascii=True) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Construct-tool token budget benchmark")
    p.add_argument("--python-dir", required=True)
    p.add_argument("--python-tools-dir", required=True)
    p.add_argument("--diamond-base-dir", required=True)
    p.add_argument("--diamond-full-dir", required=True)
    p.add_argument("--python-pattern", default="*.py")
    p.add_argument("--python-tools-pattern", default="*.py")
    p.add_argument("--diamond-base-pattern", default="*.dmd")
    p.add_argument("--diamond-full-pattern", default="*.dmd")

    p.add_argument("--tokenizer-json")
    p.add_argument("--hf-tokenizer-path")
    p.add_argument("--tokenizer-cmd")
    p.add_argument("--heuristic", action="store_true")

    p.add_argument("--append-jsonl")
    p.add_argument("--run-id")
    p.add_argument("--question", default="")
    p.add_argument("--candidate", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--out-csv", help="Optional CSV output path")

    args = p.parse_args()
    rows = build_rows(args)

    print(
        "program,python_tokens,python_with_tools,diamond_base,diamond_full,"
        "syntax_reduction,tool_overhead,net_reduction,vs_python_with_tools"
    )
    csv_lines = [
        "program,python_tokens,python_with_tools,diamond_base,diamond_full,"
        "syntax_reduction,tool_overhead,net_reduction,vs_python_with_tools"
    ]

    for r in rows:
        syn = pct(r.py - r.dm_base, r.py)
        ovh = pct(r.dm_full - r.dm_base, r.dm_base)
        net = pct(r.py - r.dm_full, r.py)
        vpt = pct(r.py_tools - r.dm_full, r.py_tools)
        line = (
            f"{r.program},{r.py},{r.py_tools},{r.dm_base},{r.dm_full},"
            f"{syn:.6f},{ovh:.6f},{net:.6f},{vpt:.6f}"
        )
        print(line)
        csv_lines.append(line)

    py_total = sum(r.py for r in rows)
    pyt_total = sum(r.py_tools for r in rows)
    dmb_total = sum(r.dm_base for r in rows)
    dmf_total = sum(r.dm_full for r in rows)

    syn = pct(py_total - dmb_total, py_total)
    ovh = pct(dmf_total - dmb_total, dmb_total)
    net = pct(py_total - dmf_total, py_total)
    vpt = pct(pyt_total - dmf_total, pyt_total)

    total_line = (
        f"TOTAL,{py_total},{pyt_total},{dmb_total},{dmf_total},"
        f"{syn:.6f},{ovh:.6f},{net:.6f},{vpt:.6f}"
    )
    print(total_line)
    csv_lines.append(total_line)

    if args.out_csv:
        out = pathlib.Path(args.out_csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")
        print(f"csv_written:{out}")

    write_jsonl(args, rows)
    if args.append_jsonl:
        print(f"jsonl_appended:{args.append_jsonl}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
