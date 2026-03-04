#!/usr/bin/env python3
"""Measure token cost of operator spellings in isolation and context."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tokenizers import Tokenizer


def tlen(tok: Tokenizer, s: str) -> int:
    return len(tok.encode(s).ids)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer-json", required=True)
    ap.add_argument("--candidates-json", required=True)
    ap.add_argument("--contexts-json", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-profile", required=True)
    ap.add_argument("--profile-name", default="qwen3-8b-q1")
    ap.add_argument("--tokenizer-name", default="Qwen/Qwen3-8B")
    args = ap.parse_args()

    tok = Tokenizer.from_file(args.tokenizer_json)
    cand = json.loads(Path(args.candidates_json).read_text(encoding="utf-8"))
    ctx = json.loads(Path(args.contexts_json).read_text(encoding="utf-8"))

    results: dict[str, list[dict[str, object]]] = {}
    winners: dict[str, str] = {}

    csv_rows = [
        "operator,candidate,isolation_tokens,context_avg,context_min,context_max,combined_score"
    ]

    for op, options in cand.items():
        templates = ctx.get(op, ["{tok}"])
        rows = []
        for opt in options:
            isolation = tlen(tok, opt)
            context_counts = [tlen(tok, tpl.format(tok=opt)) for tpl in templates]
            context_avg = sum(context_counts) / len(context_counts)
            combined = isolation + context_avg
            row = {
                "candidate": opt,
                "isolation_tokens": isolation,
                "context_tokens": context_counts,
                "context_avg": context_avg,
                "context_min": min(context_counts),
                "context_max": max(context_counts),
                "combined_score": combined,
            }
            rows.append(row)

        rows.sort(
            key=lambda r: (
                float(r["combined_score"]),
                float(r["context_avg"]),
                int(r["isolation_tokens"]),
                str(r["candidate"]),
            )
        )

        results[op] = rows
        winners[op] = str(rows[0]["candidate"])

        for r in rows:
            csv_rows.append(
                f"{op},{r['candidate']},{r['isolation_tokens']},{r['context_avg']:.4f},{r['context_min']},{r['context_max']},{r['combined_score']:.4f}"
            )

    Path(args.out_json).write_text(json.dumps(results, indent=2, ensure_ascii=True), encoding="utf-8")
    Path(args.out_csv).write_text("\n".join(csv_rows) + "\n", encoding="utf-8")

    # Compute fast greedy unique mapping (distinct surface strings across operators).
    # Order operators by confidence gap (2nd-best - best), so hard decisions lock first.
    gap_order = []
    for op, rows in results.items():
        first = float(rows[0]["combined_score"])
        second = float(rows[1]["combined_score"]) if len(rows) > 1 else first + 9999.0
        gap_order.append((second - first, op))
    gap_order.sort(reverse=True)

    used: set[str] = set()
    unique_winners: dict[str, str] = {}
    unique_score = 0.0
    for _gap, op in gap_order:
        pick = None
        for row in results[op]:
            c = str(row["candidate"])
            if c not in used:
                pick = row
                break
        if pick is None:
            pick = results[op][0]
        c = str(pick["candidate"])
        unique_winners[op] = c
        used.add(c)
        unique_score += float(pick["combined_score"])

    profile = {
        "profile": args.profile_name,
        "tokenizer": args.tokenizer_name,
        "mappings": winners,
        "mappings_unique": unique_winners,
        "method": {
            "ranking": "combined_score = isolation_tokens + context_avg",
            "contexts_per_operator": 3,
            "candidates_per_operator": 10,
            "unique_assignment": {
                "enabled": True,
                "objective": "greedy minimize combined_score with distinct candidates across operators",
                "total_score": round(unique_score, 6),
                "selection_order": [op for _gap, op in gap_order],
            },
        },
    }
    Path(args.out_profile).write_text(json.dumps(profile, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("operator,winner")
    for op in sorted(winners):
        print(f"{op},{winners[op]}")
    print("\noperator,unique_winner")
    for op in sorted(unique_winners):
        print(f"{op},{unique_winners[op]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
