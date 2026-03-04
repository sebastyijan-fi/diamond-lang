#!/usr/bin/env python3
"""Static capability composition validation for Diamond IR programs.

Rules implemented (v1):
- Declared capabilities are tool-header identifiers excluding control tools:
  `c`, `t`, `b`, `e`.
- Computed capabilities are the transitive union of:
  1) capability-sensitive builtin usage in the function body
  2) capabilities required by called local functions.
- If a function declares explicit capabilities, declaration is treated as a
  restriction ceiling and must include all computed requirements.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from diamond_ir import (
    BinaryExpr,
    CallExpr,
    ClassDecl,
    ExceptionMatchExpr,
    Expr,
    FuncDecl,
    IndexExpr,
    ListExpr,
    MapBindExpr,
    MapExpr,
    MatchExpr,
    MethodDecl,
    MemberExpr,
    NameExpr,
    PatchExpr,
    PatternLiteral,
    Program,
    PropagateExpr,
    RangeExpr,
    SequenceExpr,
    SliceExpr,
    TernaryExpr,
    TryCatchExpr,
    UnaryExpr,
)
from parse_to_ir import build_parser, iter_inputs, parse_file

CONTROL_TOOLS = {"c", "t", "b", "e"}

# v1 builtin capability map. This can grow as effectful builtins are added.
BUILTIN_CAPABILITIES: dict[str, set[str]] = {
    "slp": {"time_sleep"},
    "rnd": {"rng_uniform"},
}


@dataclass(frozen=True)
class FunctionCapabilityReport:
    name: str
    has_cap_tool: bool
    declared: tuple[str, ...]
    computed: tuple[str, ...]
    direct_callees: tuple[str, ...]
    missing: tuple[str, ...]
    extra: tuple[str, ...]


@dataclass(frozen=True)
class ProgramCapabilityReport:
    module_name: str
    functions: tuple[FunctionCapabilityReport, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _CallableDecl:
    decl: FuncDecl
    owner_class: str | None


def _collect_expr_usage(
    expr: Expr,
    local_funcs: set[str],
    owner_class: str | None,
    out_callees: set[str],
    out_builtin_caps: set[str],
) -> None:
    if isinstance(expr, CallExpr):
        if isinstance(expr.func, NameExpr):
            callee = expr.func.name
            if callee in local_funcs:
                out_callees.add(callee)
            out_builtin_caps.update(BUILTIN_CAPABILITIES.get(callee, set()))
        elif (
            owner_class is not None
            and isinstance(expr.func, MemberExpr)
            and isinstance(expr.func.obj, NameExpr)
            and expr.func.obj.name == "self"
        ):
            method_callee = f"{owner_class}__{expr.func.name}"
            if method_callee in local_funcs:
                out_callees.add(method_callee)
        _collect_expr_usage(expr.func, local_funcs, owner_class, out_callees, out_builtin_caps)
        for arg in expr.args:
            _collect_expr_usage(arg, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, UnaryExpr):
        _collect_expr_usage(expr.expr, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, BinaryExpr):
        _collect_expr_usage(expr.left, local_funcs, owner_class, out_callees, out_builtin_caps)
        _collect_expr_usage(expr.right, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, TernaryExpr):
        _collect_expr_usage(expr.cond, local_funcs, owner_class, out_callees, out_builtin_caps)
        _collect_expr_usage(expr.then_expr, local_funcs, owner_class, out_callees, out_builtin_caps)
        _collect_expr_usage(expr.else_expr, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, SequenceExpr):
        for item in expr.items:
            _collect_expr_usage(item, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, MatchExpr):
        _collect_expr_usage(expr.subject, local_funcs, owner_class, out_callees, out_builtin_caps)
        for arm in expr.arms:
            if isinstance(arm.pattern, PatternLiteral):
                _collect_expr_usage(arm.pattern.literal, local_funcs, owner_class, out_callees, out_builtin_caps)
            _collect_expr_usage(arm.expr, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, MemberExpr):
        _collect_expr_usage(expr.obj, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, IndexExpr):
        _collect_expr_usage(expr.obj, local_funcs, owner_class, out_callees, out_builtin_caps)
        _collect_expr_usage(expr.index, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, SliceExpr):
        _collect_expr_usage(expr.obj, local_funcs, owner_class, out_callees, out_builtin_caps)
        if expr.start is not None:
            _collect_expr_usage(expr.start, local_funcs, owner_class, out_callees, out_builtin_caps)
        if expr.end is not None:
            _collect_expr_usage(expr.end, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, PatchExpr):
        _collect_expr_usage(expr.obj, local_funcs, owner_class, out_callees, out_builtin_caps)
        for item in expr.items:
            _collect_expr_usage(item.value, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, MapBindExpr):
        _collect_expr_usage(expr.base, local_funcs, owner_class, out_callees, out_builtin_caps)
        _collect_expr_usage(expr.value, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, RangeExpr):
        _collect_expr_usage(expr.start, local_funcs, owner_class, out_callees, out_builtin_caps)
        _collect_expr_usage(expr.end, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, PropagateExpr):
        _collect_expr_usage(expr.expr, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, ExceptionMatchExpr):
        _collect_expr_usage(expr.exc, local_funcs, owner_class, out_callees, out_builtin_caps)
        for t in expr.types:
            _collect_expr_usage(t, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, TryCatchExpr):
        _collect_expr_usage(expr.body, local_funcs, owner_class, out_callees, out_builtin_caps)
        _collect_expr_usage(expr.handler, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, ListExpr):
        for item in expr.items:
            _collect_expr_usage(item, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    if isinstance(expr, MapExpr):
        for item in expr.items:
            _collect_expr_usage(item.value, local_funcs, owner_class, out_callees, out_builtin_caps)
        return

    # NameExpr / NumberExpr / StringExpr / BoolExpr / ReraiseExpr are leaf nodes.


def _declared_capabilities(decl: FuncDecl) -> set[str]:
    return {t for t in decl.tools if t not in CONTROL_TOOLS}


def _callable_decls(program: Program) -> dict[str, _CallableDecl]:
    out: dict[str, _CallableDecl] = {}
    for decl in program.decls:
        if isinstance(decl, FuncDecl):
            out[decl.name] = _CallableDecl(decl=decl, owner_class=None)
        elif isinstance(decl, MethodDecl):
            out[f"{decl.class_name}__{decl.func_decl.name}"] = _CallableDecl(
                decl=decl.func_decl, owner_class=decl.class_name
            )
        elif isinstance(decl, ClassDecl):
            continue
    return out


def validate_program_capabilities(program: Program, strict_extra: bool = False) -> ProgramCapabilityReport:
    by_name = _callable_decls(program)
    local_funcs = set(by_name.keys())

    direct_callees: dict[str, set[str]] = {}
    direct_builtin_caps: dict[str, set[str]] = {}
    declared_caps: dict[str, set[str]] = {}
    has_cap_tool: dict[str, bool] = {}

    for name in sorted(local_funcs):
        callable_decl = by_name[name]
        decl = callable_decl.decl
        callees: set[str] = set()
        builtin_caps: set[str] = set()
        _collect_expr_usage(decl.body, local_funcs, callable_decl.owner_class, callees, builtin_caps)
        if name in callees:
            callees.remove(name)
        direct_callees[name] = callees
        direct_builtin_caps[name] = builtin_caps
        declared_caps[name] = _declared_capabilities(decl)
        has_cap_tool[name] = "c" in decl.tools

    inferred: dict[str, set[str]] = {name: set(direct_builtin_caps[name]) for name in local_funcs}
    changed = True
    while changed:
        changed = False
        for name in local_funcs:
            next_caps = set(direct_builtin_caps[name])
            for callee in direct_callees[name]:
                next_caps.update(inferred[callee])
            if next_caps != inferred[name]:
                inferred[name] = next_caps
                changed = True

    errors: list[str] = []
    warnings: list[str] = []
    fn_reports: list[FunctionCapabilityReport] = []

    for name in sorted(local_funcs):
        decl = by_name[name].decl
        declared = declared_caps[name]
        computed = inferred[name]
        missing = set()
        extra = set()

        if declared:
            missing = computed - declared
            extra = declared - computed
            if missing:
                errors.append(
                    f"{program.module_name}:{name}: declared capabilities {sorted(declared)} "
                    f"missing required {sorted(missing)} (computed={sorted(computed)})"
                )
            if extra:
                msg = (
                    f"{program.module_name}:{name}: declared capabilities {sorted(declared)} "
                    f"include unused {sorted(extra)} (computed={sorted(computed)})"
                )
                if strict_extra:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        else:
            if computed and not has_cap_tool[name]:
                warnings.append(
                    f"{program.module_name}:{name}: inferred capabilities {sorted(computed)} "
                    "without capability marker 'c' (inference-only mode)"
                )

        if declared and not has_cap_tool[name]:
            warnings.append(
                f"{program.module_name}:{name}: explicit capabilities declared without tool 'c'"
            )

        fn_reports.append(
            FunctionCapabilityReport(
                name=name,
                has_cap_tool=has_cap_tool[name],
                declared=tuple(sorted(declared)),
                computed=tuple(sorted(computed)),
                direct_callees=tuple(sorted(direct_callees[name])),
                missing=tuple(sorted(missing)),
                extra=tuple(sorted(extra)),
            )
        )

    return ProgramCapabilityReport(
        module_name=program.module_name,
        functions=tuple(fn_reports),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _validate_paths(paths: list[Path], strict_extra: bool) -> tuple[int, int]:
    parser = build_parser()
    total_modules = 0
    total_functions = 0
    total_errors = 0
    total_warnings = 0

    for path in paths:
        inputs = iter_inputs(path)
        if not inputs:
            print(f"skip {path}: no .dmd files")
            continue
        for dm in inputs:
            program = parse_file(dm, parser=parser)
            report = validate_program_capabilities(program, strict_extra=strict_extra)
            total_modules += 1
            total_functions += len(report.functions)
            for fn in report.functions:
                declared = ",".join(fn.declared) if fn.declared else "-"
                computed = ",".join(fn.computed) if fn.computed else "-"
                callees = ",".join(fn.direct_callees) if fn.direct_callees else "-"
                print(
                    "module={m} fn={f} cap_tool={c} declared=[{d}] computed=[{r}] callees=[{k}]".format(
                        m=report.module_name,
                        f=fn.name,
                        c=("yes" if fn.has_cap_tool else "no"),
                        d=declared,
                        r=computed,
                        k=callees,
                    )
                )
            for msg in report.warnings:
                total_warnings += 1
                print(f"warning: {msg}")
            for msg in report.errors:
                total_errors += 1
                print(f"error: {msg}")

    print(
        "capability_validation_summary: "
        f"modules={total_modules} functions={total_functions} "
        f"warnings={total_warnings} errors={total_errors}"
    )
    return total_errors, total_warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond capability composition (static).")
    ap.add_argument(
        "--in",
        dest="inputs",
        action="append",
        required=True,
        help="Input .dmd file or directory (repeatable)",
    )
    ap.add_argument(
        "--strict-extra",
        action="store_true",
        help="Treat unused declared capabilities as errors",
    )
    ap.add_argument(
        "--max-warnings",
        type=int,
        default=-1,
        help="Fail if total warnings exceed this count (-1 disables warning cap)",
    )
    args = ap.parse_args(argv)

    paths = [Path(p) for p in args.inputs]
    errors, warnings = _validate_paths(paths, strict_extra=args.strict_extra)
    if errors:
        return 1
    if args.max_warnings >= 0 and warnings > args.max_warnings:
        print(
            "capability_validation_gate_fail: "
            f"warnings={warnings} > max_warnings={args.max_warnings}"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
