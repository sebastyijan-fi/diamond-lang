#!/usr/bin/env python3
"""Validate Diamond completeness inventory CSV and emit status reports."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REQUIRED_COLUMNS = (
    "id",
    "domain",
    "item",
    "tier",
    "status",
    "spec_ref",
    "implementation_ref",
    "tests_ref",
    "gate_ref",
    "rationale",
    "compensating_mechanism",
    "notes",
)

ALLOWED_STATUS = {
    "implemented",
    "intentionally_excluded",
    "partially_implemented",
    "gap_identified",
}

ALLOWED_TIERS = {"universal", "common", "specialized", "rare"}


@dataclass(frozen=True)
class Violation:
    row_index: int
    row_id: str
    message: str


def _cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _is_empty(value: str) -> bool:
    return value.strip() == ""


def _iter_refs(value: str) -> Iterable[str]:
    raw = value.strip()
    if not raw:
        return ()
    parts = [p.strip() for p in raw.split("|")]
    return tuple(p for p in parts if p)


def _check_ref_paths(
    row_index: int,
    row_id: str,
    field_name: str,
    field_value: str,
    violations: list[Violation],
) -> None:
    for ref in _iter_refs(field_value):
        path = Path(ref)
        if not path.exists():
            violations.append(
                Violation(
                    row_index=row_index,
                    row_id=row_id,
                    message=f"{field_name} references missing path: {ref}",
                )
            )


def validate_rows(
    rows: list[dict[str, str]],
    require_gate_ref_for_implemented: bool,
    check_paths: bool,
) -> list[Violation]:
    violations: list[Violation] = []
    seen_ids: set[str] = set()

    for index, row in enumerate(rows, start=2):
        row_id = _cell(row, "id")
        domain = _cell(row, "domain")
        item = _cell(row, "item")
        tier = _cell(row, "tier")
        status = _cell(row, "status")
        spec_ref = _cell(row, "spec_ref")
        implementation_ref = _cell(row, "implementation_ref")
        tests_ref = _cell(row, "tests_ref")
        gate_ref = _cell(row, "gate_ref")
        rationale = _cell(row, "rationale")
        compensating = _cell(row, "compensating_mechanism")

        if _is_empty(row_id):
            violations.append(Violation(index, row_id, "id is required"))
        elif row_id in seen_ids:
            violations.append(Violation(index, row_id, "duplicate id"))
        else:
            seen_ids.add(row_id)

        if _is_empty(domain):
            violations.append(Violation(index, row_id, "domain is required"))
        if _is_empty(item):
            violations.append(Violation(index, row_id, "item is required"))
        if tier not in ALLOWED_TIERS:
            violations.append(
                Violation(
                    index,
                    row_id,
                    f"tier must be one of {sorted(ALLOWED_TIERS)} (got: {tier or '<empty>'})",
                )
            )
        if status not in ALLOWED_STATUS:
            violations.append(
                Violation(
                    index,
                    row_id,
                    f"status must be one of {sorted(ALLOWED_STATUS)} (got: {status or '<empty>'})",
                )
            )

        if status == "implemented":
            if _is_empty(spec_ref):
                violations.append(Violation(index, row_id, "implemented requires spec_ref"))
            if _is_empty(implementation_ref):
                violations.append(
                    Violation(index, row_id, "implemented requires implementation_ref")
                )
            if _is_empty(tests_ref):
                violations.append(Violation(index, row_id, "implemented requires tests_ref"))
            if require_gate_ref_for_implemented and _is_empty(gate_ref):
                violations.append(Violation(index, row_id, "implemented requires gate_ref"))

        if status == "partially_implemented":
            if _is_empty(rationale):
                violations.append(
                    Violation(index, row_id, "partially_implemented requires rationale")
                )

        if status == "intentionally_excluded":
            if _is_empty(rationale):
                violations.append(
                    Violation(index, row_id, "intentionally_excluded requires rationale")
                )
            if _is_empty(compensating):
                violations.append(
                    Violation(
                        index,
                        row_id,
                        "intentionally_excluded requires compensating_mechanism",
                    )
                )

        if check_paths:
            for field_name, field_value in (
                ("spec_ref", spec_ref),
                ("implementation_ref", implementation_ref),
                ("tests_ref", tests_ref),
                ("gate_ref", gate_ref),
            ):
                _check_ref_paths(index, row_id, field_name, field_value, violations)

    return violations


def build_report(rows: list[dict[str, str]]) -> str:
    totals_by_status = Counter(_cell(r, "status") for r in rows)
    domain_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        domain_status_counts[_cell(row, "domain")][_cell(row, "status")] += 1

    freeze_ready = all(
        _cell(row, "status") in {"implemented", "intentionally_excluded"} for row in rows
    )

    lines: list[str] = []
    lines.append("# Diamond Completeness Status Report")
    lines.append("")
    lines.append(
        f"Generated: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    lines.append("")
    lines.append(f"Total items: **{len(rows)}**")
    lines.append(f"Freeze-ready shape: **{'yes' if freeze_ready else 'no'}**")

    implemented = totals_by_status.get("implemented", 0)
    intentionally_excluded = totals_by_status.get("intentionally_excluded", 0)
    classified = implemented + intentionally_excluded
    implemented_pct = implemented / len(rows) * 100 if rows else 0
    classified_pct = classified / len(rows) * 100 if rows else 0

    lines.append(f"Implementation coverage: **{implemented_pct:.1f}%**")
    lines.append(f"Classified baseline coverage: **{classified_pct:.1f}%**")
    lines.append("")
    lines.append("")
    lines.append("## Status totals")
    lines.append("")
    lines.append("| status | count |")
    lines.append("|---|---:|")
    for status in sorted(ALLOWED_STATUS):
        lines.append(f"| {status} | {totals_by_status.get(status, 0)} |")
    lines.append("")
    lines.append("## Domain breakdown")
    lines.append("")
    lines.append("| domain | implemented | intentionally_excluded | partially_implemented | gap_identified |")
    lines.append("|---|---:|---:|---:|---:|")
    for domain in sorted(domain_status_counts):
        c = domain_status_counts[domain]
        lines.append(
            f"| {domain} | {c.get('implemented', 0)} | {c.get('intentionally_excluded', 0)} | {c.get('partially_implemented', 0)} | {c.get('gap_identified', 0)} |"
        )
    lines.append("")
    lines.append("## Outstanding items")
    lines.append("")
    for row in rows:
        status = _cell(row, "status")
        if status in {"gap_identified", "partially_implemented"}:
            lines.append(f"- `{_cell(row, 'id')}` ({_cell(row, 'domain')}): {status}")
    if lines[-1] == "":
        # keep markdown stable if there are no outstanding items
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate docs/completeness/completeness_inventory.csv contract."
    )
    parser.add_argument(
        "--csv",
        default="docs/completeness/completeness_inventory.csv",
        help="Path to completeness inventory CSV",
    )
    parser.add_argument(
        "--report-out",
        default="docs/completeness/STATUS_REPORT.md",
        help="Write markdown report to this path. Use '-' to disable writing.",
    )
    parser.add_argument(
        "--no-require-gate-ref-for-implemented",
        action="store_true",
        help="Allow implemented rows with empty gate_ref",
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Fail if any path in *_ref columns does not exist",
    )
    parser.add_argument(
        "--min-classified-coverage",
        type=float,
        default=100.0,
        help=(
            "Fail if classified baseline coverage (implemented + intentionally_excluded) "
            "falls below this percentage"
        ),
    )
    parser.add_argument(
        "--min-implementation-coverage",
        type=float,
        default=0.0,
        help="Fail if implemented coverage falls below this percentage",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"FAIL: missing csv file: {csv_path}")
        return 2

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing_columns = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
        if missing_columns:
            print(f"FAIL: missing required columns: {', '.join(missing_columns)}")
            return 2
        rows = list(reader)

    if not rows:
        print("FAIL: completeness inventory is empty")
        return 2

    violations = validate_rows(
        rows=rows,
        require_gate_ref_for_implemented=not args.no_require_gate_ref_for_implemented,
        check_paths=args.check_paths,
    )

    status_counts = Counter(_cell(r, "status") for r in rows)
    total_rows = len(rows)
    implemented = status_counts.get("implemented", 0)
    intentionally_excluded = status_counts.get("intentionally_excluded", 0)
    classified = implemented + intentionally_excluded
    classified_coverage = classified / total_rows * 100 if total_rows else 0
    implementation_coverage = implemented / total_rows * 100 if total_rows else 0

    print(f"rows={len(rows)}")
    print(f"classified_coverage={classified_coverage:.1f}")
    print(f"implementation_coverage={implementation_coverage:.1f}")
    for status in sorted(ALLOWED_STATUS):
        print(f"{status}={status_counts.get(status, 0)}")

    if classified_coverage + 1e-9 < args.min_classified_coverage:
        print(
            f"FAIL: classified baseline coverage {classified_coverage:.1f}% below minimum "
            f"{args.min_classified_coverage:.1f}%"
        )
        return 1
    if implementation_coverage + 1e-9 < args.min_implementation_coverage:
        print(
            f"FAIL: implementation coverage {implementation_coverage:.1f}% below minimum "
            f"{args.min_implementation_coverage:.1f}%"
        )
        return 1

    if violations:
        print(f"FAIL: {len(violations)} validation violation(s)")
        for v in violations:
            row_label = v.row_id or "<missing-id>"
            print(f"  row {v.row_index} [{row_label}] {v.message}")
        return 1

    if args.report_out != "-":
        report = build_report(rows)
        report_path = Path(args.report_out)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print(f"report_written={report_path}")

    print("OK: completeness inventory validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
