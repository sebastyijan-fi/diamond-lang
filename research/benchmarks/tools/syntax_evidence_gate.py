#!/usr/bin/env python3
"""Statistical evidence gate for Diamond syntax/cost changes.

Compares baseline vs candidate construct-tool benchmark CSVs (from
construct_tool_bench.py) and enforces improvement thresholds.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

POSITIVE_BETTER = {"syntax_reduction", "net_reduction", "vs_python_with_tools"}
LOWER_BETTER = {"tool_overhead"}


@dataclass(frozen=True)
class SeriesStats:
    mean: float
    median: float
    p95: float


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return math.nan
    if len(values) == 1:
        return values[0]
    s = sorted(values)
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    weight = pos - lo
    return s[lo] * (1.0 - weight) + s[hi] * weight


def _stats(values: list[float]) -> SeriesStats:
    if not values:
        raise ValueError("empty values")
    return SeriesStats(
        mean=sum(values) / len(values),
        median=_quantile(values, 0.5),
        p95=_quantile(values, 0.95),
    )


def _read_metric(csv_path: Path, metric: str) -> dict[str, float]:
    rows: dict[str, float] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"program", metric}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"{csv_path}: missing columns: {sorted(missing)}")
        for row in r:
            program = (row.get("program") or "").strip()
            if not program or program == "TOTAL":
                continue
            val = float(row[metric])
            rows[program] = val
    if not rows:
        raise ValueError(f"{csv_path}: no program rows found")
    return rows


def _aggregate(files: list[Path], metric: str) -> dict[str, float]:
    per_file = [_read_metric(p, metric) for p in files]
    common = set(per_file[0].keys())
    for rows in per_file[1:]:
        common &= set(rows.keys())
    if not common:
        raise ValueError("no common program stems across provided csv files")
    out: dict[str, float] = {}
    for k in sorted(common):
        out[k] = sum(rows[k] for rows in per_file) / len(per_file)
    return out


def _improvement(metric: str, baseline: float, candidate: float) -> float:
    if metric in POSITIVE_BETTER:
        return candidate - baseline
    if metric in LOWER_BETTER:
        return baseline - candidate
    raise ValueError(f"unsupported metric: {metric}")


def _bootstrap_mean_ci(
    improvements: list[float],
    *,
    n_samples: int,
    alpha: float,
    seed: int,
) -> tuple[float, float, float]:
    rnd = random.Random(seed)
    n = len(improvements)
    means: list[float] = []
    for _ in range(n_samples):
        sample = [improvements[rnd.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    lower = _quantile(means, alpha / 2.0)
    upper = _quantile(means, 1.0 - alpha / 2.0)
    prob_pos = sum(1 for x in means if x > 0.0) / len(means)
    return lower, upper, prob_pos


def _csv_paths(raws: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in raws:
        for part in raw.split(","):
            p = part.strip()
            if p:
                out.append(Path(p))
    if not out:
        raise ValueError("no csv inputs provided")
    missing = [str(p) for p in out if not p.exists()]
    if missing:
        raise ValueError(f"missing csv files: {missing}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Statistical syntax evidence gate")
    ap.add_argument(
        "--baseline-csv",
        action="append",
        required=True,
        help="Baseline CSV path(s), repeat or comma-separate values",
    )
    ap.add_argument(
        "--candidate-csv",
        action="append",
        required=True,
        help="Candidate CSV path(s), repeat or comma-separate values",
    )
    ap.add_argument(
        "--metric",
        default="net_reduction",
        choices=sorted(POSITIVE_BETTER | LOWER_BETTER),
    )
    ap.add_argument("--bootstrap-samples", type=int, default=5000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--min-programs", type=int, default=1)
    ap.add_argument("--min-mean-improvement", type=float, default=0.005)
    ap.add_argument("--min-ci-lower", type=float, default=0.0)
    ap.add_argument("--min-prob-positive", type=float, default=0.90)
    ap.add_argument("--out-json", default="")
    ap.add_argument("--out-md", default="")
    args = ap.parse_args()

    baseline_files = _csv_paths(args.baseline_csv)
    candidate_files = _csv_paths(args.candidate_csv)

    baseline = _aggregate(baseline_files, args.metric)
    candidate = _aggregate(candidate_files, args.metric)
    common = sorted(set(baseline.keys()) & set(candidate.keys()))
    if len(common) < args.min_programs:
        print(
            f"FAIL: common programs {len(common)} < min_programs {args.min_programs}"
        )
        return 2

    baseline_vals = [baseline[k] for k in common]
    candidate_vals = [candidate[k] for k in common]
    improvements = [
        _improvement(args.metric, baseline[k], candidate[k]) for k in common
    ]

    b_stats = _stats(baseline_vals)
    c_stats = _stats(candidate_vals)
    i_stats = _stats(improvements)
    ci_low, ci_high, prob_positive = _bootstrap_mean_ci(
        improvements,
        n_samples=args.bootstrap_samples,
        alpha=args.alpha,
        seed=args.seed,
    )

    pass_mean = i_stats.mean >= args.min_mean_improvement
    pass_ci = ci_low >= args.min_ci_lower
    pass_prob = prob_positive >= args.min_prob_positive
    passed = pass_mean and pass_ci and pass_prob

    report = {
        "metric": args.metric,
        "baseline_files": [str(p) for p in baseline_files],
        "candidate_files": [str(p) for p in candidate_files],
        "program_count": len(common),
        "baseline": {
            "mean": b_stats.mean,
            "median": b_stats.median,
            "p95": b_stats.p95,
        },
        "candidate": {
            "mean": c_stats.mean,
            "median": c_stats.median,
            "p95": c_stats.p95,
        },
        "improvement": {
            "mean": i_stats.mean,
            "median": i_stats.median,
            "p95": i_stats.p95,
            "ci_lower": ci_low,
            "ci_upper": ci_high,
            "prob_positive": prob_positive,
        },
        "thresholds": {
            "min_mean_improvement": args.min_mean_improvement,
            "min_ci_lower": args.min_ci_lower,
            "min_prob_positive": args.min_prob_positive,
        },
        "checks": {
            "mean": pass_mean,
            "ci_lower": pass_ci,
            "prob_positive": pass_prob,
        },
        "passed": passed,
    }

    print(f"metric={args.metric}")
    print(f"programs={len(common)}")
    print(
        f"baseline mean={b_stats.mean:.6f} median={b_stats.median:.6f} p95={b_stats.p95:.6f}"
    )
    print(
        f"candidate mean={c_stats.mean:.6f} median={c_stats.median:.6f} p95={c_stats.p95:.6f}"
    )
    print(
        "improvement "
        f"mean={i_stats.mean:.6f} median={i_stats.median:.6f} p95={i_stats.p95:.6f} "
        f"ci95=[{ci_low:.6f},{ci_high:.6f}] p(pos)={prob_positive:.4f}"
    )
    print(
        "checks "
        f"mean={pass_mean} ci_lower={pass_ci} prob_positive={pass_prob}"
    )

    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"json_written={out_json}")

    if args.out_md:
        out_md = Path(args.out_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        md = [
            "# Diamond Syntax Evidence Report",
            "",
            f"- metric: `{args.metric}`",
            f"- programs: `{len(common)}`",
            f"- passed: `{passed}`",
            "",
            "## Baseline",
            "",
            f"- mean: `{b_stats.mean:.6f}`",
            f"- median: `{b_stats.median:.6f}`",
            f"- p95: `{b_stats.p95:.6f}`",
            "",
            "## Candidate",
            "",
            f"- mean: `{c_stats.mean:.6f}`",
            f"- median: `{c_stats.median:.6f}`",
            f"- p95: `{c_stats.p95:.6f}`",
            "",
            "## Improvement (oriented positive)",
            "",
            f"- mean: `{i_stats.mean:.6f}`",
            f"- median: `{i_stats.median:.6f}`",
            f"- p95: `{i_stats.p95:.6f}`",
            f"- ci95: `[{ci_low:.6f}, {ci_high:.6f}]`",
            f"- p(improvement > 0): `{prob_positive:.4f}`",
            "",
            "## Thresholds",
            "",
            f"- min_mean_improvement: `{args.min_mean_improvement}`",
            f"- min_ci_lower: `{args.min_ci_lower}`",
            f"- min_prob_positive: `{args.min_prob_positive}`",
            "",
            "## Checks",
            "",
            f"- mean check: `{pass_mean}`",
            f"- ci check: `{pass_ci}`",
            f"- probability check: `{pass_prob}`",
            "",
        ]
        out_md.write_text("\n".join(md), encoding="utf-8")
        print(f"markdown_written={out_md}")

    if not passed:
        print("FAIL: evidence gate failed")
        return 1
    print("OK: evidence gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
