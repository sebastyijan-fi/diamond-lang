#!/usr/bin/env python3
"""Automatic Diamond language probe on real Python repos.

Pipeline:
1) clone/update repo snapshot
2) run baseline pytest when feasible
3) scan AST features across source files
4) compute Diamond core-gap pressure signals
5) emit JSON report + append measurement log
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "src" / "probing" / "reports"
REPOS_DIR = ROOT / "src" / "probing" / "repos"
DECISION_LOG = ROOT / "research" / "benchmarks" / "measurements" / "decision_log.jsonl"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug_from_url(url: str) -> str:
    s = url.rstrip("/")
    if s.endswith(".git"):
        s = s[:-4]
    return s.rsplit("/", 1)[-1]


def _run(
    cmd: list[str], cwd: Path | None = None, timeout_s: int = 240, env: dict[str, str] | None = None
) -> tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
    )
    return p.returncode, p.stdout, p.stderr


def _clone_or_update(repo_url: str, dst: Path) -> str:
    if dst.exists():
        _run(["git", "fetch", "--all", "--tags", "--prune"], cwd=dst)
        rc, out, _ = _run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=dst)
        target = out.strip() if rc == 0 and out.strip() else "origin/HEAD"
        _run(["git", "checkout", "-q", target.replace("origin/", "")], cwd=dst)
        _run(["git", "pull", "--ff-only"], cwd=dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        rc, out, err = _run(["git", "clone", "--depth", "1", repo_url, str(dst)])
        if rc != 0:
            raise RuntimeError(f"git clone failed: {err or out}")

    rc, out, err = _run(["git", "rev-parse", "--short", "HEAD"], cwd=dst)
    if rc != 0:
        raise RuntimeError(f"git rev-parse failed: {err or out}")
    return out.strip()


def _find_license_text(repo: Path) -> str:
    names = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
    for n in names:
        p = repo / n
        if p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="ignore")[:20000]
            except Exception:
                return ""
    return ""


def _detect_license_kind(text: str) -> str:
    t = text.lower()
    if "mit license" in t:
        return "MIT"
    if "apache license" in t and "version 2.0" in t:
        return "Apache-2.0"
    if (
        "redistribution and use in source and binary forms" in t
        and ("neither the name of the copyright holder" in t or "neither the name of" in t)
    ):
        return "BSD-3-Clause"
    if "bsd 3-clause" in t:
        return "BSD-3-Clause"
    if "bsd 2-clause" in t:
        return "BSD-2-Clause"
    if "mozilla public license" in t:
        return "MPL"
    return "unknown"


def _has_pytest(repo: Path) -> bool:
    if (repo / "tests").exists():
        return True
    for p in [repo / "pyproject.toml", repo / "setup.cfg", repo / "tox.ini"]:
        if p.exists():
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if "pytest" in txt:
                return True
    return False


def _run_baseline_tests(repo: Path) -> dict[str, Any]:
    if not _has_pytest(repo):
        return {
            "attempted": False,
            "reason": "pytest_not_detected",
            "exit_code": None,
            "summary": "",
        }
    env = os.environ.copy()
    path_parts = [str(repo)]
    if (repo / "src").exists():
        path_parts.insert(0, str(repo / "src"))
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(path_parts + ([existing] if existing else []))

    rc, out, err = _run([sys.executable, "-m", "pytest", "-q"], cwd=repo, timeout_s=300, env=env)
    text = (out + "\n" + err).strip()

    def _summary(s: str) -> str:
        for line in reversed(s.splitlines()):
            if re.search(r"\b(passed|failed|error|errors|xfailed|xpassed|skipped)\b", line):
                return line.strip()
        return ""

    summary = _summary(text)
    result: dict[str, Any] = {
        "attempted": True,
        "exit_code": rc,
        "summary": summary,
        "output_tail": "\n".join(text.splitlines()[-25:]),
    }

    # Fallback for repos where CLI tests fail only because console-script entry points
    # are not installed in probe mode.
    if (
        rc != 0
        and ("test_cli" in text or "cli.py" in text)
        and ("No such file or directory" in text or "FileNotFoundError" in text)
    ):
        rc2, out2, err2 = _run(
            [sys.executable, "-m", "pytest", "-q", "-k", "not cli"],
            cwd=repo,
            timeout_s=300,
            env=env,
        )
        text2 = (out2 + "\n" + err2).strip()
        result.update(
            {
                "fallback_used": True,
                "fallback_filter": "not cli",
                "fallback_exit_code": rc2,
                "fallback_summary": _summary(text2),
                "fallback_output_tail": "\n".join(text2.splitlines()[-25:]),
            }
        )
    return result


@dataclass
class FeatureCounts:
    file_count: int = 0
    class_def: int = 0
    func_def: int = 0
    async_func_def: int = 0
    decorator_use: int = 0
    with_stmt: int = 0
    async_with_stmt: int = 0
    for_stmt: int = 0
    while_stmt: int = 0
    try_stmt: int = 0
    raise_stmt: int = 0
    yield_expr: int = 0
    lambda_expr: int = 0
    list_comp: int = 0
    set_comp: int = 0
    dict_comp: int = 0
    gen_exp: int = 0
    match_stmt: int = 0
    named_expr: int = 0
    max_function_nesting: int = 0


class _Counter(ast.NodeVisitor):
    def __init__(self) -> None:
        self.c = FeatureCounts()
        self._depth = 0

    def _enter(self) -> None:
        self._depth += 1
        self.c.max_function_nesting = max(self.c.max_function_nesting, self._depth)

    def _exit(self) -> None:
        self._depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.c.class_def += 1
        self.c.decorator_use += len(node.decorator_list)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.c.func_def += 1
        self.c.decorator_use += len(node.decorator_list)
        self._enter()
        self.generic_visit(node)
        self._exit()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self.c.async_func_def += 1
        self.c.decorator_use += len(node.decorator_list)
        self._enter()
        self.generic_visit(node)
        self._exit()

    def visit_With(self, node: ast.With) -> Any:
        self.c.with_stmt += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> Any:
        self.c.async_with_stmt += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> Any:
        self.c.for_stmt += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> Any:
        self.c.while_stmt += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> Any:
        self.c.try_stmt += 1
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> Any:
        self.c.raise_stmt += 1
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield) -> Any:
        self.c.yield_expr += 1
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> Any:
        self.c.yield_expr += 1
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> Any:
        self.c.lambda_expr += 1
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> Any:
        self.c.list_comp += 1
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> Any:
        self.c.set_comp += 1
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> Any:
        self.c.dict_comp += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> Any:
        self.c.gen_exp += 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> Any:  # py311+
        self.c.match_stmt += 1
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> Any:
        self.c.named_expr += 1
        self.generic_visit(node)


def _iter_source_files(repo: Path) -> list[Path]:
    ignored_dirs = {
        ".git",
        ".venv",
        "venv",
        "build",
        "dist",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "tests",
        "testing",
        "docs",
        "benchmarks",
    }
    files: list[Path] = []
    for p in repo.rglob("*.py"):
        if any(part in ignored_dirs for part in p.parts):
            continue
        files.append(p)
    return files


def _scan_features(repo: Path) -> FeatureCounts:
    counter = _Counter()
    files = _iter_source_files(repo)
    counter.c.file_count = len(files)
    for p in files:
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(p))
            counter.visit(tree)
        except SyntaxError:
            continue
    return counter.c


def _gap_signals(c: FeatureCounts) -> dict[str, Any]:
    signals: list[dict[str, Any]] = []

    def add(name: str, severity: str, count: int, note: str) -> None:
        if count > 0:
            signals.append({"name": name, "severity": severity, "count": count, "note": note})

    add("class_model", "high", c.class_def, "Direct class syntax/object semantics gap for full ports.")
    add("decorators", "high", c.decorator_use, "Decorator-heavy APIs need first-class lowering profile.")
    add("async_model", "high", c.async_func_def + c.async_with_stmt, "Async semantics are not in Diamond core.")
    add("context_managers", "medium", c.with_stmt + c.async_with_stmt, "with/async with requires effect-boundary model.")
    add("generator_model", "high", c.yield_expr + c.gen_exp, "yield/generator semantics need core design.")
    add("loop_statements", "medium", c.for_stmt + c.while_stmt, "Statement loops may need compact canonical form.")
    add("exception_flow", "medium", c.try_stmt + c.raise_stmt, "Exception paths are supported but high-volume stress target.")
    add("comprehensions", "low", c.list_comp + c.set_comp + c.dict_comp, "Could be lowered via map/fold; assess token tradeoff.")

    score = (
        5 * c.class_def
        + 4 * (c.async_func_def + c.async_with_stmt)
        + 3 * c.decorator_use
        + 3 * (c.yield_expr + c.gen_exp)
        + 2 * (c.with_stmt + c.for_stmt + c.while_stmt)
        + 1 * (c.try_stmt + c.raise_stmt + c.list_comp + c.dict_comp + c.set_comp)
    )
    return {"friction_score": score, "signals": sorted(signals, key=lambda x: (-x["count"], x["name"]))}


def _append_decision_log(payload: dict[str, Any]) -> None:
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DECISION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-url", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--run-tests", action="store_true")
    args = ap.parse_args()

    name = args.name or _slug_from_url(args.repo_url)
    repo_dir = REPOS_DIR / name

    commit = _clone_or_update(args.repo_url, repo_dir)
    license_kind = _detect_license_kind(_find_license_text(repo_dir))
    test_result = _run_baseline_tests(repo_dir) if args.run_tests else {"attempted": False}
    features = _scan_features(repo_dir)
    gaps = _gap_signals(features)

    ts = _now_utc()
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_probe_{name}"
    report = {
        "record_type": "probe_repo_report",
        "ts_utc": ts,
        "run_id": run_id,
        "repo_url": args.repo_url,
        "repo_name": name,
        "commit": commit,
        "license": license_kind,
        "tests": test_result,
        "features": asdict(features),
        "gaps": gaps,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"{run_id}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    _append_decision_log(
        {
            "record_type": "probe_repo_measurement",
            "ts_utc": ts,
            "run_id": run_id,
            "question": "language_gap_probe",
            "candidate": "auto_probe",
            "project": name,
            "repo_url": args.repo_url,
            "commit": commit,
            "license": license_kind,
            "tests_attempted": bool(test_result.get("attempted")),
            "tests_exit_code": test_result.get("exit_code"),
            "tests_summary": test_result.get("summary", ""),
            "file_count": features.file_count,
            "class_def": features.class_def,
            "decorator_use": features.decorator_use,
            "async_total": features.async_func_def + features.async_with_stmt,
            "with_total": features.with_stmt + features.async_with_stmt,
            "yield_total": features.yield_expr + features.gen_exp,
            "loop_total": features.for_stmt + features.while_stmt,
            "exception_total": features.try_stmt + features.raise_stmt,
            "friction_score": gaps["friction_score"],
            "report_file": str(out.relative_to(ROOT)),
            "notes": "Automatic probe for Diamond core-gap pressure.",
        }
    )

    print(f"probe report: {out}")
    print(
        json.dumps(
            {
                "project": name,
                "commit": commit,
                "license": license_kind,
                "tests": test_result,
                "friction_score": gaps["friction_score"],
                "top_signals": gaps["signals"][:5],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
