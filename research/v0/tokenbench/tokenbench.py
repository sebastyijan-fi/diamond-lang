#!/usr/bin/env python3
"""Compare token counts across syntax variants.

Supports:
- Hugging Face tokenizer from a local path
- External command with {file} placeholder
- Heuristic fallback tokenizer (regex) for quick local iteration
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class CaseResult:
    name: str
    path: str
    tokens: int


def list_cases(cases_dir: pathlib.Path, pattern: str) -> list[pathlib.Path]:
    files = sorted(cases_dir.glob(pattern))
    if not files:
        raise SystemExit(f"No files found in {cases_dir} matching pattern {pattern!r}")
    return files


def count_with_cmd(path: pathlib.Path, cmd_template: str) -> int:
    if "{file}" not in cmd_template:
        raise SystemExit("--tokenizer-cmd must include {file} placeholder")
    cmd = cmd_template.replace("{file}", shlex.quote(str(path)))
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(
            f"Tokenizer command failed for {path.name}:\n{proc.stderr.strip()}"
        )
    out = proc.stdout.strip()
    m = re.search(r"(\d+)", out)
    if not m:
        raise SystemExit(
            f"Tokenizer command for {path.name} did not output an integer."
        )
    return int(m.group(1))


def count_with_hf(path: pathlib.Path, tokenizer_path: str) -> int:
    try:
        from transformers import AutoTokenizer  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "transformers is not installed. Use --tokenizer-cmd or --heuristic."
        ) from exc

    tok = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    text = path.read_text(encoding="utf-8")
    return len(tok.encode(text, add_special_tokens=False))


def count_with_tokenizer_json(path: pathlib.Path, tokenizer_json: str) -> int:
    try:
        from tokenizers import Tokenizer  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "tokenizers is not installed. Use --tokenizer-cmd or --heuristic."
        ) from exc

    tok = Tokenizer.from_file(tokenizer_json)
    text = path.read_text(encoding="utf-8")
    return len(tok.encode(text).ids)


def count_with_heuristic(path: pathlib.Path) -> int:
    # Fast rough proxy: split words and punctuation.
    text = path.read_text(encoding="utf-8")
    parts = re.findall(r"[A-Za-z_][A-Za-z_0-9]*|\d+\.\d+|\d+|\S", text)
    return len(parts)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def tokenizer_meta(args: argparse.Namespace) -> tuple[str, str]:
    if args.tokenizer_json:
        return "tokenizer_json", args.tokenizer_json
    if args.hf_tokenizer_path:
        return "hf", args.hf_tokenizer_path
    if args.tokenizer_cmd:
        return "cmd", args.tokenizer_cmd
    if args.heuristic:
        return "heuristic", "regex_proxy"
    return "unknown", "unknown"


def build_run_id(args: argparse.Namespace) -> str:
    if args.run_id:
        return args.run_id
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{stamp}"


def append_jsonl_records(
    args: argparse.Namespace,
    results: list[CaseResult],
    best: CaseResult,
    worst: CaseResult,
    delta: int,
    pct: float,
) -> None:
    path = pathlib.Path(args.append_jsonl)
    path.parent.mkdir(parents=True, exist_ok=True)

    run_id = build_run_id(args)
    backend, ref = tokenizer_meta(args)

    with path.open("a", encoding="utf-8") as fh:
        for r in results:
            rec = {
                "record_type": "measurement",
                "ts_utc": utc_now_iso(),
                "run_id": run_id,
                "question": args.question,
                "candidate": args.candidate,
                "program": r.name,
                "file": r.path,
                "tokens": r.tokens,
                "tokenizer_backend": backend,
                "tokenizer_ref": ref,
                "notes": args.notes,
            }
            fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

        summary = {
            "record_type": "summary",
            "ts_utc": utc_now_iso(),
            "run_id": run_id,
            "question": args.question,
            "candidate": args.candidate,
            "files_measured": len(results),
            "best_program": best.name,
            "best_tokens": best.tokens,
            "worst_program": worst.name,
            "worst_tokens": worst.tokens,
            "spread_tokens": delta,
            "spread_pct_vs_worst": round(pct, 4),
            "tokenizer_backend": backend,
            "tokenizer_ref": ref,
            "notes": args.notes,
        }
        fh.write(json.dumps(summary, ensure_ascii=True) + "\n")


def run(args: argparse.Namespace) -> int:
    cases_dir = pathlib.Path(args.cases_dir)
    files = list_cases(cases_dir, args.pattern)

    results: list[CaseResult] = []
    for path in files:
        if args.tokenizer_json:
            count = count_with_tokenizer_json(path, args.tokenizer_json)
        elif args.hf_tokenizer_path:
            count = count_with_hf(path, args.hf_tokenizer_path)
        elif args.tokenizer_cmd:
            count = count_with_cmd(path, args.tokenizer_cmd)
        elif args.heuristic:
            count = count_with_heuristic(path)
        else:
            raise SystemExit(
                "Choose one backend: --tokenizer-json, --hf-tokenizer-path, --tokenizer-cmd, or --heuristic"
            )
        results.append(CaseResult(name=path.name, path=str(path), tokens=count))

    results.sort(key=lambda r: r.tokens)

    print("variant,tokens")
    for r in results:
        print(f"{r.name},{r.tokens}")

    best = results[0]
    worst = results[-1]
    delta = worst.tokens - best.tokens
    pct = 0.0 if worst.tokens == 0 else (delta / worst.tokens) * 100.0
    print()
    print(f"best:  {best.name} ({best.tokens})")
    print(f"worst: {worst.name} ({worst.tokens})")
    print(f"spread: {delta} tokens ({pct:.2f}% vs worst)")

    if args.append_jsonl:
        append_jsonl_records(args, results, best, worst, delta, pct)
        print(f"jsonl_appended: {args.append_jsonl}")

    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Token count benchmark for Diamond syntax variants")
    p.add_argument("--cases-dir", default="cases", help="Directory containing .dm case files")
    p.add_argument("--pattern", default="*.dm", help="Glob pattern for case files (default: *.dm)")
    p.add_argument("--tokenizer-json", help="Path to tokenizer.json file (uses `tokenizers` backend)")
    p.add_argument("--hf-tokenizer-path", help="Local Hugging Face tokenizer path")
    p.add_argument(
        "--tokenizer-cmd",
        help="External command template containing {file}, e.g. 'mytok {file}'",
    )
    p.add_argument("--heuristic", action="store_true", help="Use regex heuristic tokenizer")
    p.add_argument("--append-jsonl", help="Append structured measurement records to JSONL path")
    p.add_argument("--run-id", help="Run identifier for JSONL records (default: auto-generated UTC id)")
    p.add_argument("--question", default="", help="Design question identifier for JSONL records")
    p.add_argument("--candidate", default="", help="Candidate syntax identifier for JSONL records")
    p.add_argument("--notes", default="", help="Optional notes attached to JSONL records")
    return p.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args(sys.argv[1:])))
