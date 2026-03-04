#!/usr/bin/env python3
"""Module-system benchmark for Diamond B-core and C-contract modes.

Computes per-program and portfolio metrics from a cases directory containing:
- {name}_singlefile.dmd
- {name}_multiblock.dmd
- optional {name}_context.dmd (C-contract context pack)

Records are appended to decision_log.jsonl with stable fields so D10+ decisions
can be compared across runs.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_run_id(run_id: str | None) -> str:
    if run_id:
        return run_id
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{stamp}_module_system"


@dataclass
class ProgramFiles:
    name: str
    singlefile: pathlib.Path
    multiblock: pathlib.Path
    context: pathlib.Path | None


BLOCK_OPEN_RE = re.compile(r"@([A-Za-z_][A-Za-z_0-9]*)(?:\[[^\]]*\])?\{", re.M)
QUAL_REF_RE = re.compile(r"\b([A-Za-z_][A-Za-z_0-9]*)\.")


def discover_programs(cases_dir: pathlib.Path) -> list[ProgramFiles]:
    singles = sorted(cases_dir.glob("*_singlefile.dmd"))
    if not singles:
        raise SystemExit(f"No *_singlefile.dmd found under {cases_dir}")

    programs: list[ProgramFiles] = []
    for sf in singles:
        base = sf.name[: -len("_singlefile.dmd")]
        mf = cases_dir / f"{base}_multiblock.dmd"
        if not mf.exists():
            raise SystemExit(f"Missing multiblock for {base}: {mf}")
        ctx = cases_dir / f"{base}_context.dmd"
        programs.append(ProgramFiles(name=base, singlefile=sf, multiblock=mf, context=(ctx if ctx.exists() else None)))
    return programs


def count_with_hf(text: str, tokenizer_path: str) -> int:
    from transformers import AutoTokenizer  # type: ignore

    tok = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    return len(tok.encode(text, add_special_tokens=False))


def count_with_tokenizer_json(text: str, tokenizer_json: str) -> int:
    from tokenizers import Tokenizer  # type: ignore

    tok = Tokenizer.from_file(tokenizer_json)
    return len(tok.encode(text).ids)


def count_with_heuristic(text: str) -> int:
    parts = re.findall(r"[A-Za-z_][A-Za-z_0-9]*|\d+\.\d+|\d+|\S", text)
    return len(parts)


def count_text(text: str, args: argparse.Namespace) -> int:
    if args.tokenizer_json:
        return count_with_tokenizer_json(text, args.tokenizer_json)
    if args.hf_tokenizer_path:
        return count_with_hf(text, args.hf_tokenizer_path)
    if args.heuristic:
        return count_with_heuristic(text)
    raise SystemExit("Choose one backend: --tokenizer-json, --hf-tokenizer-path, or --heuristic")


def tokenizer_meta(args: argparse.Namespace) -> tuple[str, str]:
    if args.tokenizer_json:
        return "tokenizer_json", args.tokenizer_json
    if args.hf_tokenizer_path:
        return "hf", args.hf_tokenizer_path
    return "heuristic", "regex_proxy"


def parse_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        m = BLOCK_OPEN_RE.search(text, i)
        if not m:
            break
        name = m.group(1)
        body_start = m.end()
        depth = 1
        j = body_start
        while j < n and depth > 0:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            j += 1
        if depth != 0:
            # Unbalanced braces: treat remaining tail as body for diagnostics.
            blocks.append((name, text[body_start:]))
            break
        body = text[body_start : j - 1]
        blocks.append((name, body))
        i = j
    return blocks


def edge_counts_from_multiblock(text: str) -> tuple[int, int]:
    blocks = parse_blocks(text)
    block_names = {b for b, _ in blocks}
    edge_occ = 0
    unique_edges: set[tuple[str, str]] = set()

    for src, body in blocks:
        for m in QUAL_REF_RE.finditer(body):
            tgt = m.group(1)
            if tgt in block_names and tgt != src:
                edge_occ += 1
                unique_edges.add((src, tgt))

    return edge_occ, len(unique_edges)


def context_split(text: str) -> tuple[str, str]:
    contract_lines: list[str] = []
    body_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#@") or stripped.startswith("//@"):
            contract_lines.append(line)
        else:
            body_lines.append(line)
    contract = "\n".join(contract_lines).strip()
    body = "\n".join(body_lines).strip()
    return contract, body


def parse_clean(files: list[pathlib.Path]) -> bool:
    # Parser check mirrors existing regression intent: deterministic parse, zero ambiguities.
    transpiler_dir = pathlib.Path(__file__).resolve().parents[2] / "transpiler_v0"
    sys.path.insert(0, str(transpiler_dir))
    try:
        from parse_to_ir import build_parser, parse_source, _extract_module_blocks  # type: ignore
    except Exception:
        return False

    parser = build_parser()
    for p in files:
        src = p.read_text(encoding="utf-8")
        try:
            blocks = _extract_module_blocks(src, p.name)
            if blocks is None:
                parse_source(src, module_name=p.name, parser=parser)
            else:
                # Ambiguity gate checks parseability of each block body, independent of
                # cross-block semantic resolution (matches historical D10 methodology).
                for b in blocks:
                    parse_source(b.body, module_name=f"{p.name}@{b.name}", parser=parser)
        except Exception:
            return False
    return True


def append_jsonl(path: pathlib.Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=True) + "\n")


def run(args: argparse.Namespace) -> int:
    cases_dir = pathlib.Path(args.cases_dir)
    programs = discover_programs(cases_dir)
    run_id = build_run_id(args.run_id)
    backend, ref = tokenizer_meta(args)
    log_path = pathlib.Path(args.append_jsonl)

    per_rows: list[dict[str, Any]] = []

    for pr in programs:
        single_text = pr.singlefile.read_text(encoding="utf-8")
        multi_text = pr.multiblock.read_text(encoding="utf-8")
        single_tokens = count_text(single_text, args)
        multi_tokens = count_text(multi_text, args)

        edge_occ, unique_edges = edge_counts_from_multiblock(multi_text)
        overhead = multi_tokens - single_tokens
        structure = (overhead / single_tokens) if single_tokens else 0.0
        tpe = (overhead / edge_occ) if edge_occ else 0.0

        row: dict[str, Any] = {
            "program": pr.name,
            "singlefile_tokens": single_tokens,
            "multiblock_tokens": multi_tokens,
            "overhead_tokens": overhead,
            "structure_overhead": structure,
            "edge_occurrences": edge_occ,
            "unique_edges": unique_edges,
            "tokens_per_edge": tpe,
            "gate_structure_overhead_le_10pct": structure <= 0.10,
            "gate_tokens_per_edge_le_2": tpe <= 2.0,
        }

        if pr.context is not None:
            ctx_text = pr.context.read_text(encoding="utf-8")
            ctx_tokens = count_text(ctx_text, args)
            ctext, btext = context_split(ctx_text)
            contract_tokens = count_text(ctext, args) if ctext else 0
            body_tokens = count_text(btext, args) if btext else 0
            row.update(
                {
                    "context_tokens": ctx_tokens,
                    "contract_tokens": contract_tokens,
                    "active_body_tokens": body_tokens,
                    "context_vs_multiblock_reduction": ((multi_tokens - ctx_tokens) / multi_tokens) if multi_tokens else 0.0,
                    "context_vs_singlefile_reduction": ((single_tokens - ctx_tokens) / single_tokens) if single_tokens else 0.0,
                    "contract_share_of_context": (contract_tokens / ctx_tokens) if ctx_tokens else 0.0,
                }
            )

        per_rows.append(row)

    parse_files = [r.multiblock for r in programs]
    parse_files.extend([r.context for r in programs if r.context is not None])
    ambiguity_clean = parse_clean([p for p in parse_files if p is not None])

    print(
        "program,multiblock,singlefile,overhead,structure_overhead,edge_occurrences,unique_edges,tokens_per_edge,context_tokens,contract_tokens,active_body_tokens,context_vs_multiblock_reduction"
    )
    for r in per_rows:
        print(
            ",".join(
                [
                    str(r.get("program", "")),
                    str(r.get("multiblock_tokens", "")),
                    str(r.get("singlefile_tokens", "")),
                    str(r.get("overhead_tokens", "")),
                    f"{r.get('structure_overhead', 0.0):.6f}",
                    str(r.get("edge_occurrences", "")),
                    str(r.get("unique_edges", "")),
                    f"{r.get('tokens_per_edge', 0.0):.6f}",
                    str(r.get("context_tokens", "")),
                    str(r.get("contract_tokens", "")),
                    str(r.get("active_body_tokens", "")),
                    ("" if "context_vs_multiblock_reduction" not in r else f"{r.get('context_vs_multiblock_reduction', 0.0):.6f}"),
                ]
            )
        )

    total_multi = sum(int(r["multiblock_tokens"]) for r in per_rows)
    total_single = sum(int(r["singlefile_tokens"]) for r in per_rows)
    total_overhead = total_multi - total_single
    total_edges = sum(int(r["edge_occurrences"]) for r in per_rows)
    total_structure = (total_overhead / total_single) if total_single else 0.0
    total_tpe = (total_overhead / total_edges) if total_edges else 0.0

    has_context = any("context_tokens" in r for r in per_rows)
    total_ctx = sum(int(r.get("context_tokens", 0)) for r in per_rows)
    total_contract = sum(int(r.get("contract_tokens", 0)) for r in per_rows)
    total_body = sum(int(r.get("active_body_tokens", 0)) for r in per_rows)

    print()
    print(
        f"portfolio: multiblock={total_multi} singlefile={total_single} overhead={total_overhead} structure_overhead={total_structure:.6f} edge_occ={total_edges} tokens_per_edge={total_tpe:.6f} ambiguity_parse_clean={str(ambiguity_clean).lower()}"
    )
    if has_context:
        ctx_reduction = ((total_multi - total_ctx) / total_multi) if total_multi else 0.0
        print(
            f"portfolio_context: context_tokens={total_ctx} contract_tokens={total_contract} active_body_tokens={total_body} context_vs_multiblock_reduction={ctx_reduction:.6f}"
        )

    if args.append_jsonl:
        for r in per_rows:
            rec = {
                "record_type": "module_system_measurement",
                "ts_utc": utc_now_iso(),
                "run_id": run_id,
                "question": args.question,
                "candidate": args.candidate,
                "program": r["program"],
                "multiblock_tokens": r["multiblock_tokens"],
                "singlefile_tokens": r["singlefile_tokens"],
                "overhead_tokens": r["overhead_tokens"],
                "structure_overhead": r["structure_overhead"],
                "edge_occurrences": r["edge_occurrences"],
                "unique_edges": r["unique_edges"],
                "tokens_per_edge": r["tokens_per_edge"],
                "gate_structure_overhead_le_10pct": r["gate_structure_overhead_le_10pct"],
                "gate_tokens_per_edge_le_2": r["gate_tokens_per_edge_le_2"],
                "tokenizer_backend": backend,
                "tokenizer_ref": ref,
                "notes": args.notes,
            }
            if "context_tokens" in r:
                rec.update(
                    {
                        "context_tokens": r["context_tokens"],
                        "contract_tokens": r["contract_tokens"],
                        "active_body_tokens": r["active_body_tokens"],
                        "context_vs_multiblock_reduction": r["context_vs_multiblock_reduction"],
                        "context_vs_singlefile_reduction": r["context_vs_singlefile_reduction"],
                        "contract_share_of_context": r["contract_share_of_context"],
                    }
                )
            append_jsonl(log_path, rec)

        summary: dict[str, Any] = {
            "record_type": "module_system_summary",
            "ts_utc": utc_now_iso(),
            "run_id": run_id,
            "question": args.question,
            "candidate": args.candidate,
            "files_measured": len(per_rows),
            "multiblock_tokens_total": total_multi,
            "singlefile_tokens_total": total_single,
            "overhead_tokens_total": total_overhead,
            "structure_overhead": total_structure,
            "edge_occurrences_total": total_edges,
            "tokens_per_edge": total_tpe,
            "ambiguity_parse_clean": ambiguity_clean,
            "gate_structure_overhead_le_10pct_all": all(bool(r["gate_structure_overhead_le_10pct"]) for r in per_rows),
            "gate_tokens_per_edge_le_2_all": all(bool(r["gate_tokens_per_edge_le_2"]) for r in per_rows),
            "tokenizer_backend": backend,
            "tokenizer_ref": ref,
            "notes": args.notes,
        }
        if has_context:
            summary.update(
                {
                    "context_tokens_total": total_ctx,
                    "contract_tokens_total": total_contract,
                    "active_body_tokens_total": total_body,
                    "context_vs_multiblock_reduction": ((total_multi - total_ctx) / total_multi) if total_multi else 0.0,
                }
            )
        append_jsonl(log_path, summary)
        print(f"jsonl_appended: {log_path}")

    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark Diamond module-system overhead/context metrics")
    p.add_argument("--cases-dir", required=True, help="Directory with *_singlefile.dmd and *_multiblock.dmd")
    p.add_argument("--tokenizer-json", help="Path to tokenizer.json")
    p.add_argument("--hf-tokenizer-path", help="Local HF tokenizer path")
    p.add_argument("--heuristic", action="store_true", help="Regex heuristic token counter")
    p.add_argument("--append-jsonl", default="", help="Decision log JSONL path")
    p.add_argument("--run-id", default="", help="Run id for JSONL records")
    p.add_argument("--question", default="module_system_metrics", help="Question key for JSONL records")
    p.add_argument("--candidate", default="", help="Candidate key for JSONL records")
    p.add_argument("--notes", default="", help="Optional notes")
    return p.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args(sys.argv[1:])))
