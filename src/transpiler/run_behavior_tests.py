#!/usr/bin/env python3
"""Behavioral equivalence checks for transpiled Diamond programs."""

from __future__ import annotations

import argparse
import copy
import importlib.util
from dataclasses import dataclass
import math
from pathlib import Path
import sys
from typing import Any, Callable

from transpile import main as transpile_main


def _id(x: Any) -> Any:
    return x


def _ops3_to_objs(args: tuple[Any, ...]) -> tuple[Any, ...]:
    ops = args[0]
    out = [{"k": cmd, "a": key, "v": value} for cmd, key, value in ops]
    return (out,)


def _ops2_to_objs(args: tuple[Any, ...]) -> tuple[Any, ...]:
    ops = args[0]
    out = [{"k": cmd, "v": value} for cmd, value in ops]
    return (out,)


def _ops_event_to_objs(args: tuple[Any, ...]) -> tuple[Any, ...]:
    ops = args[0]
    out = [{"k": cmd, "e": event, "v": value} for cmd, event, value in ops]
    return (out,)


def _events_rate_to_objs(args: tuple[Any, ...]) -> tuple[Any, ...]:
    events, cap, rate = args
    out = [{"t": t, "c": cost} for t, cost in events]
    return (out, cap, rate)


def _canon_http_gen(out: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    code = int(out["c"])
    body = out["b"]
    if "u" in body:
        return code, {"users": body["u"]}
    if "s" in body:
        return code, {"status": body["s"]}
    if "e" in body:
        msg = body["e"]
        msg = {"nf": "not found", "mna": "method not allowed"}.get(msg, msg)
        return code, {"error": msg}
    return code, body


def _canon_retry_gen(out: dict[str, Any]) -> tuple[bool, int, list[int]]:
    return bool(out["ok"]), int(out["tries"]), list(out["wait"])


def _deep_equal(a: Any, b: Any) -> bool:
    """Semantic equality for behavior checks.

    Handles NaN equivalence and nested structures so parser-heavy suites do not
    report false negatives on values that are semantically equal in context.
    """
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_deep_equal(a[k], b[k]) for k in a.keys())
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_deep_equal(x, y) for x, y in zip(a, b))
    return a == b


@dataclass(frozen=True)
class ProgramSpec:
    slug: str
    generated_fn: str
    cases: list[tuple[Any, ...]]
    adapt_gen_args: Callable[[tuple[Any, ...]], tuple[Any, ...]] = _id
    adapt_ref_args: Callable[[tuple[Any, ...]], tuple[Any, ...]] = _id
    canon_gen_out: Callable[[Any], Any] = _id
    canon_ref_out: Callable[[Any], Any] = _id


PROGRAMS: dict[str, ProgramSpec] = {
    "02_fibonacci_recursive_iterative": ProgramSpec(
        slug="02_fibonacci_recursive_iterative",
        generated_fn="fb",
        cases=[(0,), (1,), (2,), (10,), (20,), (30,)],
    ),
    "03_json_parser_simplified": ProgramSpec(
        slug="03_json_parser_simplified",
        generated_fn="jp",
        cases=[("",), ("42",), ('{"a":1}',), ("[1,2,3]",), ("not json",)],
    ),
    "01_fizzbuzz": ProgramSpec(
        slug="01_fizzbuzz",
        generated_fn="fz",
        cases=[(0,), (1,), (3,), (15,)],
    ),
    "04_url_router": ProgramSpec(
        slug="04_url_router",
        generated_fn="rt",
        cases=[("/",), ("/users",), ("/health",), ("/missing",)],
    ),
    "06_http_handler_routing": ProgramSpec(
        slug="06_http_handler_routing",
        generated_fn="h",
        cases=[("GET", "/users"), ("GET", "/health"), ("GET", "/missing"), ("POST", "/users")],
        canon_gen_out=_canon_http_gen,
    ),
    "07_key_value_store_memory": ProgramSpec(
        slug="07_key_value_store_memory",
        generated_fn="kv",
        cases=[
            (
                [
                    ("set", "a", "1"),
                    ("get", "a", ""),
                    ("get", "b", ""),
                    ("del", "a", ""),
                    ("get", "a", ""),
                ],
            ),
            (
                [
                    ("set", "x", "7"),
                    ("set", "x", "8"),
                    ("get", "x", ""),
                    ("del", "x", ""),
                    ("get", "x", ""),
                ],
            ),
        ],
        adapt_gen_args=_ops3_to_objs,
    ),
    "08_csv_parser": ProgramSpec(
        slug="08_csv_parser",
        generated_fn="csv",
        cases=[("a,b\nc,d",), ("  a,b\nc,d  ",), ("a,b\n",)],
    ),
    "09_binary_search": ProgramSpec(
        slug="09_binary_search",
        generated_fn="bs",
        cases=[
            ([1, 3, 5, 7, 9], 1),
            ([1, 3, 5, 7, 9], 5),
            ([1, 3, 5, 7, 9], 9),
            ([1, 3, 5, 7, 9], 2),
            ([], 1),
            ([2], 2),
            ([2], 3),
            ([1, 2, 2, 2, 3], 2),
        ],
    ),
    "10_merge_sort": ProgramSpec(
        slug="10_merge_sort",
        generated_fn="ms",
        cases=[([],), ([1],), ([2, 1],), ([3, 1, 2],), ([5, 4, 3, 2, 1],), ([1, 2, 3],), ([3, 3, 1, 2, 1],)],
    ),
    "11_stack": ProgramSpec(
        slug="11_stack",
        generated_fn="st",
        cases=[
            ([("push", 1), ("push", 2), ("pop", 0), ("pop", 0), ("pop", 0)],),
            ([("pop", 0), ("push", 7), ("pop", 0), ("push", 9), ("push", 3), ("pop", 0)],),
        ],
        adapt_gen_args=_ops2_to_objs,
    ),
    "12_queue": ProgramSpec(
        slug="12_queue",
        generated_fn="qu",
        cases=[
            ([("deq", 0)],),
            ([("enq", 1), ("enq", 2), ("deq", 0), ("deq", 0)],),
            ([("enq", 7), ("deq", 0), ("deq", 0)],),
            ([("enq", 1), ("enq", 2), ("enq", 3), ("deq", 0), ("deq", 0), ("deq", 0)],),
            ([("enq", 9), ("enq", 8), ("deq", 0), ("enq", 1), ("deq", 0)],),
        ],
        adapt_gen_args=_ops2_to_objs,
    ),
    "15_event_emitter": ProgramSpec(
        slug="15_event_emitter",
        generated_fn="ev",
        cases=[
            ([("on", "a", "x"), ("emit", "a", ""), ("emit", "b", ""), ("on", "a", "y"), ("emit", "a", "")],),
            ([("on", "e", "h1"), ("on", "e", "h2"), ("emit", "e", "")],),
        ],
        adapt_gen_args=_ops_event_to_objs,
    ),
    "16_retry_exponential_backoff": ProgramSpec(
        slug="16_retry_exponential_backoff",
        generated_fn="rt",
        cases=[
            ([True], 100, 5),
            ([False, True], 100, 5),
            ([False, False, False], 50, 2),
            ([], 100, 3),
        ],
        canon_gen_out=_canon_retry_gen,
    ),
    "05_rate_limiter_token_bucket": ProgramSpec(
        slug="05_rate_limiter_token_bucket",
        generated_fn="rl",
        cases=[
            ([], 5, 1),
            ([(0, 1), (0, 1), (0, 1), (0, 1)], 3, 1),
            ([(0, 1), (3, 1), (3, 2), (4, 3)], 5, 1),
            ([(0, 3), (1, 3), (2, 3), (3, 3)], 4, 1),
            ([(0, 2), (10, 1), (10, 5), (11, 1)], 5, 2),
        ],
        adapt_gen_args=_events_rate_to_objs,
    ),
}


BATCHES: dict[str, list[str]] = {
    "p02": ["02_fibonacci_recursive_iterative"],
    "p12": ["12_queue"],
    "p05": ["05_rate_limiter_token_bucket"],
    "p03": ["03_json_parser_simplified"],
    "batch1": ["01_fizzbuzz", "04_url_router"],
    "batch2": ["07_key_value_store_memory", "11_stack"],
    "batch3": ["08_csv_parser", "16_retry_exponential_backoff"],
    "batch4": ["06_http_handler_routing", "15_event_emitter"],
    "hard_math": ["09_binary_search", "10_merge_sort"],
    "all_profile10": [
        "01_fizzbuzz",
        "04_url_router",
        "06_http_handler_routing",
        "07_key_value_store_memory",
        "08_csv_parser",
        "09_binary_search",
        "10_merge_sort",
        "11_stack",
        "15_event_emitter",
        "16_retry_exponential_backoff",
    ],
    "all_portfolio14_v4": [
        "01_fizzbuzz",
        "02_fibonacci_recursive_iterative",
        "03_json_parser_simplified",
        "04_url_router",
        "05_rate_limiter_token_bucket",
        "06_http_handler_routing",
        "07_key_value_store_memory",
        "08_csv_parser",
        "09_binary_search",
        "10_merge_sort",
        "11_stack",
        "12_queue",
        "15_event_emitter",
        "16_retry_exponential_backoff",
    ],
}


def _load_module(path: Path, alias: str):
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(alias, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _transpile(in_dir: Path, out_dir: Path) -> None:
    rc = transpile_main(
        [
            "--in",
            str(in_dir),
            "--backend",
            "python",
            "--out-dir",
            str(out_dir),
            "--dump-ir-json",
        ]
    )
    if rc != 0:
        raise RuntimeError(f"transpile failed with code {rc}")


def run(programs: list[str], in_dir: Path, out_dir: Path, ref_dir: Path) -> int:
    _transpile(in_dir, out_dir)

    total = 0
    failed = 0
    lines: list[str] = []
    lines.append("program,case,result")

    for slug in programs:
        spec = PROGRAMS[slug]
        gen_path = out_dir / f"{slug}.py"
        ref_path = ref_dir / f"{slug}.py"
        if not gen_path.exists():
            raise RuntimeError(f"missing generated module: {gen_path}")
        if not ref_path.exists():
            raise RuntimeError(f"missing reference module: {ref_path}")

        gen_mod = _load_module(gen_path, f"gen_{slug}")
        ref_mod = _load_module(ref_path, f"ref_{slug}")

        gen_fn = getattr(gen_mod, spec.generated_fn)
        ref_fn = getattr(ref_mod, "solve")

        for idx, args in enumerate(spec.cases, start=1):
            total += 1
            raw = copy.deepcopy(args)
            gen_args = spec.adapt_gen_args(copy.deepcopy(raw))
            ref_args = spec.adapt_ref_args(copy.deepcopy(raw))

            got = spec.canon_gen_out(gen_fn(*gen_args))
            expected = spec.canon_ref_out(ref_fn(*ref_args))
            ok = _deep_equal(got, expected)
            if not ok:
                failed += 1
                lines.append(f"{slug},#{idx},FAIL expected={expected!r} got={got!r}")
            else:
                lines.append(f"{slug},#{idx},PASS")

    print("\n".join(lines))
    print(f"\nsummary: {total - failed}/{total} passing")
    return 1 if failed else 0


def _resolve_programs(batch: str | None, programs: str | None) -> list[str]:
    selected: list[str] = []
    if batch:
        if batch not in BATCHES:
            raise RuntimeError(f"unknown batch: {batch} (supported: {', '.join(sorted(BATCHES))})")
        selected.extend(BATCHES[batch])
    if programs:
        selected.extend([p.strip() for p in programs.split(",") if p.strip()])
    if not selected:
        selected = BATCHES["hard_math"]

    out: list[str] = []
    for s in selected:
        if s not in PROGRAMS:
            raise RuntimeError(f"unsupported program requested: {s}")
        if s not in out:
            out.append(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Diamond->Python behavioral checks against reference implementations.")
    ap.add_argument("--batch", default=None, help=f"Batch preset: {', '.join(sorted(BATCHES))}")
    ap.add_argument("--programs", default=None, help="Comma-separated program slugs (overrides/adds to --batch).")
    ap.add_argument("--in-dir", default="docs/decisions/profile_v1/programs")
    ap.add_argument("--out-dir", default="src/transpiler/out/python_exec")
    ap.add_argument("--ref-dir", default="research/benchmarks/corpus/reference_python_profile10")
    args = ap.parse_args()

    return run(
        _resolve_programs(args.batch, args.programs),
        Path(args.in_dir),
        Path(args.out_dir),
        Path(args.ref_dir),
    )


if __name__ == "__main__":
    raise SystemExit(main())
