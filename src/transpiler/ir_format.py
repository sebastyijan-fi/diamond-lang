"""Helpers for rendering Diamond IR nodes for emitter comments/logging."""

from __future__ import annotations

from diamond_ir import (
    BinaryExpr,
    BoolExpr,
    CallExpr,
    ExceptionMatchExpr,
    Expr,
    IndexExpr,
    ListExpr,
    MapBindExpr,
    MapExpr,
    MatchExpr,
    MemberExpr,
    NameExpr,
    NumberExpr,
    PatchExpr,
    PatternIdent,
    PatternLiteral,
    PatternWild,
    PropagateExpr,
    ReraiseExpr,
    RangeExpr,
    SequenceExpr,
    SliceExpr,
    StringExpr,
    TernaryExpr,
    TryCatchExpr,
    TypeExpr,
    TypeList,
    TypeName,
    TypeRecord,
    UnaryExpr,
)


def type_to_text(t: TypeExpr) -> str:
    if isinstance(t, TypeName):
        return t.name
    if isinstance(t, TypeList):
        return f"[{type_to_text(t.inner)}]"
    if isinstance(t, TypeRecord):
        body = ",".join(f"{f.name}:{type_to_text(f.type_expr)}" for f in t.fields)
        return "{" + body + "}"
    return "?"


def _pattern_to_text(p: PatternWild | PatternIdent | PatternLiteral) -> str:
    if isinstance(p, PatternWild):
        return "_"
    if isinstance(p, PatternIdent):
        return p.name
    if isinstance(p, PatternLiteral):
        return expr_to_text(p.literal)
    return "_"


def expr_to_text(e: Expr) -> str:
    if isinstance(e, NameExpr):
        return e.name
    if isinstance(e, NumberExpr):
        return e.value
    if isinstance(e, StringExpr):
        return e.value
    if isinstance(e, BoolExpr):
        return "true" if e.value else "false"
    if isinstance(e, ListExpr):
        return "[" + ",".join(expr_to_text(x) for x in e.items) + "]"
    if isinstance(e, MapExpr):
        items = ",".join(f"{i.key}:{expr_to_text(i.value)}" for i in e.items)
        return "{" + items + "}"
    if isinstance(e, UnaryExpr):
        return f"{e.op}{expr_to_text(e.expr)}"
    if isinstance(e, BinaryExpr):
        return f"({expr_to_text(e.left)}{e.op}{expr_to_text(e.right)})"
    if isinstance(e, TernaryExpr):
        return f"({expr_to_text(e.cond)}?{expr_to_text(e.then_expr)}:{expr_to_text(e.else_expr)})"
    if isinstance(e, SequenceExpr):
        return ";".join(expr_to_text(x) for x in e.items)
    if isinstance(e, MatchExpr):
        arms = "".join(f"~{_pattern_to_text(a.pattern)}:{expr_to_text(a.expr)}" for a in e.arms)
        return expr_to_text(e.subject) + arms
    if isinstance(e, CallExpr):
        return f"{expr_to_text(e.func)}(" + ",".join(expr_to_text(a) for a in e.args) + ")"
    if isinstance(e, MemberExpr):
        return f"{expr_to_text(e.obj)}.{e.name}"
    if isinstance(e, IndexExpr):
        return f"{expr_to_text(e.obj)}[{expr_to_text(e.index)}]"
    if isinstance(e, SliceExpr):
        a = expr_to_text(e.start) if e.start is not None else ""
        b = expr_to_text(e.end) if e.end is not None else ""
        return f"{expr_to_text(e.obj)}[{a}:{b}]"
    if isinstance(e, PatchExpr):
        items = ",".join(f"{i.key}:{expr_to_text(i.value)}" for i in e.items)
        return f"{expr_to_text(e.obj)}{{{items}}}"
    if isinstance(e, MapBindExpr):
        return f"{expr_to_text(e.base)}#{e.key}:{expr_to_text(e.value)}"
    if isinstance(e, RangeExpr):
        return f"{expr_to_text(e.start)}..{expr_to_text(e.end)}"
    if isinstance(e, PropagateExpr):
        return f"{expr_to_text(e.expr)}?"
    if isinstance(e, ExceptionMatchExpr):
        return "isexc(" + ",".join(expr_to_text(x) for x in [e.exc, *e.types]) + ")"
    if isinstance(e, ReraiseExpr):
        return "reraise"
    if isinstance(e, TryCatchExpr):
        return f"try({expr_to_text(e.body)},{e.err_name}:{expr_to_text(e.handler)})"
    return "<expr>"
