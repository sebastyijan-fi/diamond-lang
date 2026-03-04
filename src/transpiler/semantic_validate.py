#!/usr/bin/env python3
"""Static semantic/type validation for Diamond IR programs.

Goal: catch high-confidence semantic failures before backend emit:
- undefined symbols in value position
- invalid local/builtin call arity
- obvious type mismatches (when both sides are concrete)
- invalid `reraise` placement
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import json

from diamond_ir import (
    BinaryExpr,
    BoolExpr,
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
    NumberExpr,
    Param,
    PatchExpr,
    PatternLiteral,
    PatternIdent,
    PatternWild,
    Program,
    PropagateExpr,
    RangeExpr,
    ReraiseExpr,
    SequenceExpr,
    SliceExpr,
    StringExpr,
    TernaryExpr,
    TryCatchExpr,
    TypeExpr,
    TypeField,
    TypeList,
    TypeName,
    TypeRecord,
    UnaryExpr,
)
from parse_to_ir import build_parser, iter_inputs, parse_file


def _match_pattern_key(expr: Expr) -> str:
    if isinstance(expr, NumberExpr):
        return f"num:{expr.value}"
    if isinstance(expr, StringExpr):
        return f"str:{expr.value}"
    if isinstance(expr, BoolExpr):
        return f"bool:{str(expr.value).lower()}"
    if isinstance(expr, ListExpr):
        return "[" + ",".join(_match_pattern_key(e) for e in expr.items) + "]"
    if isinstance(expr, MapExpr):
        pairs = ",".join(
            f"{e.key if not e.key_is_string else json.dumps(e.key)}:{_match_pattern_key(e.value)}"
            for e in expr.items
        )
        return "{" + pairs + "}"
    return repr(expr)


def _validate_match_arms(expr: MatchExpr, ctx: _FnCtx) -> None:
    if not expr.arms:
        ctx.err("match expression must include at least one arm")
        return

    seen_patterns: set[str] = set()
    has_fallback = False
    for arm in expr.arms:
        if isinstance(arm.pattern, PatternWild):
            has_fallback = True
            continue
        if isinstance(arm.pattern, PatternIdent):
            has_fallback = True
            continue
        if isinstance(arm.pattern, PatternLiteral):
            key = _match_pattern_key(arm.pattern.literal)
            if key in seen_patterns:
                ctx.err(f"duplicate match literal pattern '{key}'")
                continue
            seen_patterns.add(key)
            continue
        ctx.err("unsupported match pattern kind in semantic validation")

    if not has_fallback:
        ctx.err("match expression must include a wildcard or capture arm for exhaustiveness")


@dataclass(frozen=True)
class StaticType:
    kind: str
    elem: StaticType | None = None
    fields: tuple[tuple[str, StaticType], ...] = ()
    name: str = ""


ANY_T = StaticType("any")
BOOL_T = StaticType("bool")
NUM_T = StaticType("num")
BYTE_T = StaticType("byte")
CHAR_T = StaticType("char")
STR_T = StaticType("str")
MAP_T = StaticType("map")
NONE_T = StaticType("none")
NEVER_T = StaticType("never")
FUNC_T = StaticType("func")
EXC_T = StaticType("exc")


def list_t(elem: StaticType) -> StaticType:
    return StaticType("list", elem=elem)


def record_t(fields: dict[str, StaticType]) -> StaticType:
    return StaticType("record", fields=tuple(sorted(fields.items())))


def nominal_t(name: str) -> StaticType:
    return StaticType("nominal", name=name)


def type_text(t: StaticType) -> str:
    if t.kind == "list":
        return f"[{type_text(t.elem or ANY_T)}]"
    if t.kind == "record":
        inner = ",".join(f"{k}:{type_text(v)}" for k, v in t.fields)
        return "{" + inner + "}"
    if t.kind == "nominal":
        return t.name
    return t.kind


def _looks_exception_name(name: str) -> bool:
    return name.endswith("Error") or name.endswith("Exception")


def type_from_ir(t: TypeExpr) -> StaticType:
    if isinstance(t, TypeName):
        name = t.name
        if name in {"O", "Any", "any"}:
            return ANY_T
        if name in {"Unknown", "unknown", "Top", "top"}:
            return ANY_T
        if name in {"UInt", "uint", "U32", "u32", "U64", "u64"}:
            return NUM_T
        if name in {"USize", "usize", "ISize", "isize"}:
            return NUM_T
        if name in {"Byte", "byte", "U8", "u8"}:
            return BYTE_T
        if name in {"Char", "char", "Rune", "rune"}:
            return CHAR_T
        if name in {"Bytes", "bytes", "ByteString", "bytestring"}:
            return list_t(BYTE_T)
        if name in {"I", "N", "Z", "R", "F", "Num", "num"}:
            return NUM_T
        if name in {"S", "Str", "str", "String"}:
            return STR_T
        if name in {"B", "Bool", "bool"}:
            return BOOL_T
        if name in {"M", "Map", "map"}:
            return MAP_T
        if name in {"none", "None", "Unit", "V", "Void", "void"}:
            return NONE_T
        if name in {"Never", "never", "!"}:
            return NEVER_T
        if _looks_exception_name(name):
            return EXC_T
        return nominal_t(name)

    if isinstance(t, TypeList):
        return list_t(type_from_ir(t.inner))

    if isinstance(t, TypeRecord):
        fields: dict[str, StaticType] = {}
        for fld in t.fields:
            if isinstance(fld, TypeField):
                fields[fld.name] = type_from_ir(fld.type_expr)
        return record_t(fields)

    return ANY_T


def _record_fields(t: StaticType) -> dict[str, StaticType]:
    return dict(t.fields)


def is_assignable(source: StaticType, target: StaticType) -> bool:
    if source.kind == "never":
        return True
    if source.kind == "any" or target.kind == "any":
        return True
    if source == target:
        return True

    if target.kind == "num" and source.kind in {"num", "byte"}:
        return True
    if target.kind == "byte" and source.kind == "byte":
        return True
    if target.kind == "char" and source.kind == "char":
        return True
    if target.kind == "str" and source.kind == "str":
        return True
    if target.kind == "str" and source.kind == "char":
        return True
    if target.kind == "bool" and source.kind == "bool":
        return True
    if target.kind == "none" and source.kind == "none":
        return True
    if target.kind == "exc" and source.kind in {"exc", "nominal"}:
        return source.kind == "exc" or _looks_exception_name(source.name)

    if target.kind == "map" and source.kind in {"map", "record"}:
        return True
    if target.kind == "record" and source.kind in {"record", "map"}:
        if source.kind == "map":
            return True
        src = _record_fields(source)
        for k, tv in target.fields:
            sv = src.get(k)
            if sv is None or not is_assignable(sv, tv):
                return False
        return True

    if target.kind == "list" and source.kind == "list":
        return is_assignable(source.elem or ANY_T, target.elem or ANY_T)

    if target.kind == "nominal" and source.kind == "nominal":
        return source.name == target.name

    return False


def merge_types(a: StaticType, b: StaticType) -> StaticType:
    if is_assignable(a, b):
        return b
    if is_assignable(b, a):
        return a
    if a.kind == "list" and b.kind == "list":
        return list_t(merge_types(a.elem or ANY_T, b.elem or ANY_T))
    if a.kind == "record" and b.kind == "record":
        af = _record_fields(a)
        bf = _record_fields(b)
        shared = set(af.keys()) & set(bf.keys())
        if not shared:
            return MAP_T
        return record_t({k: merge_types(af[k], bf[k]) for k in sorted(shared)})
    return ANY_T


@dataclass(frozen=True)
class BuiltinSig:
    min_args: int
    max_args: int | None
    ret: StaticType = ANY_T
    numeric_args: tuple[int, ...] = ()
    string_args: tuple[int, ...] = ()
    bool_args: tuple[int, ...] = ()


BUILTINS: dict[str, BuiltinSig] = {
    "ln": BuiltinSig(1, 1, ret=NUM_T),
    "trim": BuiltinSig(1, 1, ret=STR_T, string_args=(0,)),
    "split": BuiltinSig(2, 2, ret=list_t(STR_T), string_args=(0, 1)),
    "put": BuiltinSig(3, 3, ret=MAP_T),
    "get": BuiltinSig(3, 3, ret=ANY_T),
    "del": BuiltinSig(2, 2, ret=MAP_T),
    "jenc": BuiltinSig(1, 1, ret=STR_T),
    "jdec": BuiltinSig(1, 1, ret=ANY_T, string_args=(0,)),
    "S": BuiltinSig(1, 1, ret=STR_T),
    "I": BuiltinSig(1, 1, ret=NUM_T),
    "B": BuiltinSig(1, 1, ret=BOOL_T),
    "O": BuiltinSig(1, 1, ret=ANY_T),
    "l": BuiltinSig(1, 1, ret=list_t(ANY_T)),
    "r": BuiltinSig(1, 1, ret=list_t(ANY_T)),
    "cw": BuiltinSig(3, 3, ret=ANY_T),
    "slp": BuiltinSig(1, 1, ret=NONE_T, numeric_args=(0,)),
    "rnd": BuiltinSig(2, 2, ret=NUM_T, numeric_args=(0, 1)),
    "is_tup": BuiltinSig(1, 1, ret=BOOL_T),
    "logw": BuiltinSig(3, 3, ret=NONE_T, numeric_args=(2,)),
    "mk_retry": BuiltinSig(8, 8, ret=ANY_T),
    "mgrp": BuiltinSig(1, 2, ret=ANY_T),
    "pad6": BuiltinSig(1, 1, ret=STR_T),
    "ibase": BuiltinSig(2, 2, ret=NUM_T, string_args=(0,), numeric_args=(1,)),
    "dtd": BuiltinSig(3, 3, ret=STR_T, numeric_args=(0, 1, 2)),
    "dtt": BuiltinSig(8, 8, ret=STR_T, numeric_args=(0, 1, 2, 3, 4, 5, 6)),
    "dttm": BuiltinSig(4, 4, ret=STR_T, numeric_args=(0, 1, 2, 3)),
    "tzutc": BuiltinSig(0, 0, ret=STR_T),
    "tzoff": BuiltinSig(2, 2, ret=STR_T, numeric_args=(0, 1)),
    "q": BuiltinSig(1, 1, ret=STR_T),
    "pair": BuiltinSig(2, 2, ret=ANY_T),
    "splitln": BuiltinSig(1, 1, ret=list_t(STR_T), string_args=(0,)),
    "ini_raise": BuiltinSig(3, 3, ret=ANY_T, string_args=(0, 2), numeric_args=(1,)),
    "ini_iscommentline": BuiltinSig(1, 1, ret=BOOL_T, string_args=(0,)),
    "ini_parseline": BuiltinSig(5, 5, ret=ANY_T, string_args=(0, 1), numeric_args=(2,), bool_args=(3, 4)),
    "ini_parse_lines": BuiltinSig(2, 4, ret=list_t(ANY_T), string_args=(0,)),
    "ini_parse_ini_data": BuiltinSig(4, 4, ret=ANY_T, string_args=(0, 1), bool_args=(2, 3)),
}


EXTERNAL_VALUE_NAMES = {
    "Exception",
    "BaseException",
    "ValueError",
    "TypeError",
    "RuntimeError",
    "KeyError",
    "IndexError",
    "ZeroDivisionError",
    "AssertionError",
}


@dataclass(frozen=True)
class FunctionSig:
    params: tuple[StaticType, ...]
    ret: StaticType


@dataclass(frozen=True)
class FunctionSemanticReport:
    name: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProgramSemanticReport:
    module_name: str
    functions: tuple[FunctionSemanticReport, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass
class _FnCtx:
    module_name: str
    fn_name: str
    local_sigs: dict[str, FunctionSig]
    errors: list[str]
    warnings: list[str]
    self_field_types: dict[str, StaticType] | None = None
    self_method_sigs: dict[str, FunctionSig] | None = None
    class_shapes: dict[str, _ClassShape] | None = None

    def err(self, msg: str) -> None:
        self.errors.append(f"{self.module_name}:{self.fn_name}: {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(f"{self.module_name}:{self.fn_name}: {msg}")


@dataclass
class _ClassShape:
    fields: set[str]
    methods: set[str]
    field_types: dict[str, StaticType]
    method_sigs: dict[str, FunctionSig]


def _check_expect(ctx: _FnCtx, got: StaticType, expected: StaticType, label: str) -> None:
    if not is_assignable(got, expected):
        ctx.err(f"type mismatch for {label}: got {type_text(got)}, expected {type_text(expected)}")


def _iter_self_member_refs(expr: Expr) -> list[str]:
    refs: list[str] = []

    def walk(node: Expr) -> None:
        if isinstance(node, MemberExpr):
            if isinstance(node.obj, NameExpr) and node.obj.name == "self":
                refs.append(node.name)
            walk(node.obj)
            return
        if isinstance(node, UnaryExpr):
            walk(node.expr)
            return
        if isinstance(node, BinaryExpr):
            walk(node.left)
            walk(node.right)
            return
        if isinstance(node, TernaryExpr):
            walk(node.cond)
            walk(node.then_expr)
            walk(node.else_expr)
            return
        if isinstance(node, SequenceExpr):
            for it in node.items:
                walk(it)
            return
        if isinstance(node, MatchExpr):
            walk(node.subject)
            for arm in node.arms:
                if isinstance(arm.pattern, PatternLiteral):
                    walk(arm.pattern.literal)
                walk(arm.expr)
            return
        if isinstance(node, CallExpr):
            walk(node.func)
            for a in node.args:
                walk(a)
            return
        if isinstance(node, IndexExpr):
            walk(node.obj)
            walk(node.index)
            return
        if isinstance(node, SliceExpr):
            walk(node.obj)
            if node.start is not None:
                walk(node.start)
            if node.end is not None:
                walk(node.end)
            return
        if isinstance(node, PatchExpr):
            walk(node.obj)
            for it in node.items:
                walk(it.value)
            return
        if isinstance(node, MapBindExpr):
            walk(node.base)
            walk(node.value)
            return
        if isinstance(node, RangeExpr):
            walk(node.start)
            walk(node.end)
            return
        if isinstance(node, PropagateExpr):
            walk(node.expr)
            return
        if isinstance(node, ExceptionMatchExpr):
            walk(node.exc)
            for t in node.types:
                walk(t)
            return
        if isinstance(node, TryCatchExpr):
            walk(node.body)
            walk(node.handler)
            return
        if isinstance(node, ListExpr):
            for it in node.items:
                walk(it)
            return
        if isinstance(node, MapExpr):
            for it in node.items:
                walk(it.value)
            return
        # leaf nodes: NameExpr/NumberExpr/StringExpr/BoolExpr/ReraiseExpr

    walk(expr)
    return refs


def _iter_self_mutation_keys(expr: Expr) -> list[str]:
    keys: list[str] = []

    def walk(node: Expr) -> None:
        if isinstance(node, PatchExpr):
            if isinstance(node.obj, NameExpr) and node.obj.name == "self":
                for it in node.items:
                    keys.append(_normalized_item_key(it.key, it.key_is_string))
            walk(node.obj)
            for it in node.items:
                walk(it.value)
            return
        if isinstance(node, MapBindExpr):
            if isinstance(node.base, NameExpr) and node.base.name == "self":
                keys.append(node.key)
            walk(node.base)
            walk(node.value)
            return
        if isinstance(node, MemberExpr):
            walk(node.obj)
            return
        if isinstance(node, UnaryExpr):
            walk(node.expr)
            return
        if isinstance(node, BinaryExpr):
            walk(node.left)
            walk(node.right)
            return
        if isinstance(node, TernaryExpr):
            walk(node.cond)
            walk(node.then_expr)
            walk(node.else_expr)
            return
        if isinstance(node, SequenceExpr):
            for it in node.items:
                walk(it)
            return
        if isinstance(node, MatchExpr):
            walk(node.subject)
            for arm in node.arms:
                if isinstance(arm.pattern, PatternLiteral):
                    walk(arm.pattern.literal)
                walk(arm.expr)
            return
        if isinstance(node, CallExpr):
            walk(node.func)
            for a in node.args:
                walk(a)
            return
        if isinstance(node, IndexExpr):
            walk(node.obj)
            walk(node.index)
            return
        if isinstance(node, SliceExpr):
            walk(node.obj)
            if node.start is not None:
                walk(node.start)
            if node.end is not None:
                walk(node.end)
            return
        if isinstance(node, RangeExpr):
            walk(node.start)
            walk(node.end)
            return
        if isinstance(node, PropagateExpr):
            walk(node.expr)
            return
        if isinstance(node, ExceptionMatchExpr):
            walk(node.exc)
            for t in node.types:
                walk(t)
            return
        if isinstance(node, TryCatchExpr):
            walk(node.body)
            walk(node.handler)
            return
        if isinstance(node, ListExpr):
            for it in node.items:
                walk(it)
            return
        if isinstance(node, MapExpr):
            for it in node.items:
                walk(it.value)
            return
        # leaf nodes: NameExpr/NumberExpr/StringExpr/BoolExpr/ReraiseExpr

    walk(expr)
    return keys


def _number_literal_value(expr: Expr) -> float | None:
    if not isinstance(expr, NumberExpr):
        return None
    try:
        return float(expr.value)
    except ValueError:
        return None


def _is_byte_literal(expr: Expr) -> bool:
    if not isinstance(expr, NumberExpr):
        return False
    raw = expr.value.strip().lower()
    if "." in raw or "e" in raw:
        return False
    try:
        val = int(raw, 10)
    except ValueError:
        return False
    return 0 <= val <= 255


def _is_char_literal(expr: Expr) -> bool:
    if not isinstance(expr, StringExpr):
        return False
    raw = expr.value
    try:
        val = json.loads(raw)
    except Exception:
        val = raw.strip('"')
    return isinstance(val, str) and len(val) == 1


def _iter_self_member_calls(expr: Expr) -> list[tuple[str, int]]:
    calls: list[tuple[str, int]] = []

    def walk(node: Expr) -> None:
        if isinstance(node, CallExpr):
            if (
                isinstance(node.func, MemberExpr)
                and isinstance(node.func.obj, NameExpr)
                and node.func.obj.name == "self"
            ):
                calls.append((node.func.name, len(node.args)))
            walk(node.func)
            for a in node.args:
                walk(a)
            return
        if isinstance(node, MemberExpr):
            walk(node.obj)
            return
        if isinstance(node, UnaryExpr):
            walk(node.expr)
            return
        if isinstance(node, BinaryExpr):
            walk(node.left)
            walk(node.right)
            return
        if isinstance(node, TernaryExpr):
            walk(node.cond)
            walk(node.then_expr)
            walk(node.else_expr)
            return
        if isinstance(node, SequenceExpr):
            for it in node.items:
                walk(it)
            return
        if isinstance(node, MatchExpr):
            walk(node.subject)
            for arm in node.arms:
                if isinstance(arm.pattern, PatternLiteral):
                    walk(arm.pattern.literal)
                walk(arm.expr)
            return
        if isinstance(node, IndexExpr):
            walk(node.obj)
            walk(node.index)
            return
        if isinstance(node, SliceExpr):
            walk(node.obj)
            if node.start is not None:
                walk(node.start)
            if node.end is not None:
                walk(node.end)
            return
        if isinstance(node, PatchExpr):
            walk(node.obj)
            for it in node.items:
                walk(it.value)
            return
        if isinstance(node, MapBindExpr):
            walk(node.base)
            walk(node.value)
            return
        if isinstance(node, RangeExpr):
            walk(node.start)
            walk(node.end)
            return
        if isinstance(node, PropagateExpr):
            walk(node.expr)
            return
        if isinstance(node, ExceptionMatchExpr):
            walk(node.exc)
            for t in node.types:
                walk(t)
            return
        if isinstance(node, TryCatchExpr):
            walk(node.body)
            walk(node.handler)
            return
        if isinstance(node, ListExpr):
            for it in node.items:
                walk(it)
            return
        if isinstance(node, MapExpr):
            for it in node.items:
                walk(it.value)
            return
        # leaf nodes: NameExpr/NumberExpr/StringExpr/BoolExpr/ReraiseExpr

    walk(expr)
    return calls


def _normalized_item_key(key: str, key_is_string: bool) -> str:
    if not key_is_string:
        return key
    try:
        return str(json.loads(key))
    except Exception:
        return key.strip('"')


def _class_shapes(program: Program) -> dict[str, _ClassShape]:
    fields_by_class: dict[str, set[str]] = {}
    methods_by_class: dict[str, set[str]] = {}
    field_types_by_class: dict[str, dict[str, StaticType]] = {}
    method_sigs_by_class: dict[str, dict[str, FunctionSig]] = {}

    for decl in program.decls:
        if not isinstance(decl, ClassDecl):
            continue
        fields = {p.name for p in decl.params}
        field_types = {p.name: type_from_ir(p.type_expr) for p in decl.params}
        if isinstance(decl.body, MapExpr):
            for item in decl.body.items:
                key = _normalized_item_key(item.key, item.key_is_string)
                fields.add(key)
                field_types.setdefault(key, ANY_T)
        fields_by_class[decl.name] = fields
        methods_by_class.setdefault(decl.name, set())
        field_types_by_class[decl.name] = field_types
        method_sigs_by_class.setdefault(decl.name, {})

    for decl in program.decls:
        if not isinstance(decl, MethodDecl):
            continue
        methods_by_class.setdefault(decl.class_name, set()).add(decl.func_decl.name)
        params = tuple(type_from_ir(p.type_expr) for p in decl.func_decl.params)
        if params and decl.func_decl.params[0].name == "self":
            params = params[1:]
        method_sigs_by_class.setdefault(decl.class_name, {})[decl.func_decl.name] = FunctionSig(
            params=params,
            ret=type_from_ir(decl.func_decl.return_type),
        )
        fields_by_class.setdefault(decl.class_name, set())
        field_types_by_class.setdefault(decl.class_name, {})
        method_sigs_by_class.setdefault(decl.class_name, {})

    out: dict[str, _ClassShape] = {}
    for cname in set(fields_by_class.keys()) | set(methods_by_class.keys()):
        out[cname] = _ClassShape(
            fields=fields_by_class.get(cname, set()),
            methods=methods_by_class.get(cname, set()),
            field_types=field_types_by_class.get(cname, {}),
            method_sigs=method_sigs_by_class.get(cname, {}),
        )
    return out


def _infer_expr(expr: Expr, env: dict[str, StaticType], ctx: _FnCtx, in_handler: bool = False) -> StaticType:
    if isinstance(expr, NameExpr):
        if expr.name in env:
            return env[expr.name]
        if expr.name in {"t", "f", "true", "false"}:
            return BOOL_T
        if expr.name == "none":
            return NONE_T
        if expr.name in ctx.local_sigs:
            return FUNC_T
        if expr.name in BUILTINS:
            return FUNC_T
        if expr.name in EXTERNAL_VALUE_NAMES:
            return EXC_T if _looks_exception_name(expr.name) else ANY_T
        ctx.err(f"undefined symbol '{expr.name}'")
        return ANY_T

    if isinstance(expr, NumberExpr):
        if _is_byte_literal(expr):
            return BYTE_T
        return NUM_T
    if isinstance(expr, StringExpr):
        if _is_char_literal(expr):
            return CHAR_T
        return STR_T
    if isinstance(expr, BoolExpr):
        return BOOL_T

    if isinstance(expr, ListExpr):
        item_t = ANY_T
        for item in expr.items:
            item_t = merge_types(item_t, _infer_expr(item, env, ctx, in_handler=in_handler))
        return list_t(item_t)

    if isinstance(expr, MapExpr):
        fields: dict[str, StaticType] = {}
        all_ident_keys = True
        for item in expr.items:
            v_t = _infer_expr(item.value, env, ctx, in_handler=in_handler)
            if item.key_is_string:
                all_ident_keys = False
            fields[item.key] = v_t
        if all_ident_keys:
            return record_t(fields)
        return MAP_T

    if isinstance(expr, UnaryExpr):
        inner = _infer_expr(expr.expr, env, ctx, in_handler=in_handler)
        if expr.op == "-":
            _check_expect(ctx, inner, NUM_T, "unary '-' operand")
            return NUM_T
        return ANY_T

    if isinstance(expr, BinaryExpr):
        left = _infer_expr(expr.left, env, ctx, in_handler=in_handler)
        right = _infer_expr(expr.right, env, ctx, in_handler=in_handler)

        if expr.op in {"-", "*", "/", "%", "^", "$"}:
            if expr.op == "/":
                right_lit = _number_literal_value(expr.right)
                if right_lit == 0.0:
                    ctx.err("division by zero literal")
            if expr.op == "%":
                right_lit = _number_literal_value(expr.right)
                if right_lit == 0.0:
                    ctx.err("modulo by zero literal")
            _check_expect(ctx, left, NUM_T, f"'{expr.op}' left operand")
            _check_expect(ctx, right, NUM_T, f"'{expr.op}' right operand")
            return NUM_T

        if expr.op == "+":
            if left.kind == "any" or right.kind == "any":
                return ANY_T
            if left.kind in {"num", "byte"} and right.kind in {"num", "byte"}:
                return NUM_T
            if left.kind in {"str", "char"} and right.kind in {"str", "char"}:
                return STR_T
            if left.kind == "list" and right.kind == "list":
                return list_t(merge_types(left.elem or ANY_T, right.elem or ANY_T))
            ctx.err(
                "type mismatch for '+' operands: "
                f"left={type_text(left)} right={type_text(right)}"
            )
            return ANY_T

        if expr.op in {"==", "!=", "<", "<=", ">", ">="}:
            return BOOL_T

        if expr.op in {"&", "|"}:
            _check_expect(ctx, left, BOOL_T, f"'{expr.op}' left operand")
            _check_expect(ctx, right, BOOL_T, f"'{expr.op}' right operand")
            return BOOL_T

        return ANY_T

    if isinstance(expr, TernaryExpr):
        # Diamond v1 follows runtime truthiness for branch conditions.
        _infer_expr(expr.cond, env, ctx, in_handler=in_handler)
        then_t = _infer_expr(expr.then_expr, env, ctx, in_handler=in_handler)
        else_t = _infer_expr(expr.else_expr, env, ctx, in_handler=in_handler)
        return merge_types(then_t, else_t)

    if isinstance(expr, SequenceExpr):
        out = NONE_T
        for item in expr.items:
            out = _infer_expr(item, env, ctx, in_handler=in_handler)
        return out

    if isinstance(expr, MatchExpr):
        _validate_match_arms(expr, ctx)
        subj_t = _infer_expr(expr.subject, env, ctx, in_handler=in_handler)
        out = ANY_T
        for arm in expr.arms:
            if isinstance(arm.pattern, PatternLiteral):
                _infer_expr(arm.pattern.literal, env, ctx, in_handler=in_handler)
            arm_env = dict(env)
            if isinstance(arm.pattern, PatternIdent) and arm.pattern.name not in env:
                arm_env[arm.pattern.name] = subj_t
            arm_t = _infer_expr(arm.expr, arm_env, ctx, in_handler=in_handler)
            out = merge_types(out, arm_t)
        return out

    if isinstance(expr, CallExpr):
        if (
            isinstance(expr.func, MemberExpr)
            and isinstance(expr.func.obj, NameExpr)
            and expr.func.obj.name == "self"
        ):
            name = expr.func.name
            if ctx.self_method_sigs and name in ctx.self_method_sigs:
                sig = ctx.self_method_sigs[name]
                if len(expr.args) != len(sig.params):
                    ctx.err(
                        f"call arity mismatch for method '#.{name}': "
                        f"got {len(expr.args)}, expected {len(sig.params)}"
                    )
                for idx, arg in enumerate(expr.args):
                    arg_t = _infer_expr(arg, env, ctx, in_handler=in_handler)
                    if idx < len(sig.params):
                        _check_expect(ctx, arg_t, sig.params[idx], f"arg {idx + 1} of method '#.{name}'")
                return sig.ret

            if ctx.self_field_types and name in ctx.self_field_types:
                ctx.err(f"self member '{name}' is a field and cannot be called as method")
                for arg in expr.args:
                    _infer_expr(arg, env, ctx, in_handler=in_handler)
                return ANY_T

        if isinstance(expr.func, MemberExpr):
            obj_t = _infer_expr(expr.func.obj, env, ctx, in_handler=in_handler)
            member = expr.func.name
            if obj_t.kind == "nominal" and ctx.class_shapes and obj_t.name in ctx.class_shapes:
                shape = ctx.class_shapes[obj_t.name]
                if member in shape.method_sigs:
                    sig = shape.method_sigs[member]
                    if len(expr.args) != len(sig.params):
                        ctx.err(
                            f"call arity mismatch for method '{obj_t.name}.{member}': "
                            f"got {len(expr.args)}, expected {len(sig.params)}"
                        )
                    for idx, arg in enumerate(expr.args):
                        arg_t = _infer_expr(arg, env, ctx, in_handler=in_handler)
                        if idx < len(sig.params):
                            _check_expect(
                                ctx,
                                arg_t,
                                sig.params[idx],
                                f"arg {idx + 1} of method '{obj_t.name}.{member}'",
                            )
                    return sig.ret
                if member in shape.field_types:
                    ctx.err(
                        f"member '{obj_t.name}.{member}' is a field and cannot be called as method"
                    )
                    for arg in expr.args:
                        _infer_expr(arg, env, ctx, in_handler=in_handler)
                    return ANY_T
                ctx.err(f"unknown member '{obj_t.name}.{member}' in closed-shape class")
                for arg in expr.args:
                    _infer_expr(arg, env, ctx, in_handler=in_handler)
                return ANY_T

        if isinstance(expr.func, NameExpr):
            name = expr.func.name
            if name in {"fold", "fd"}:
                if len(expr.args) != 5:
                    ctx.err(f"{name} requires 5 arguments, got {len(expr.args)}")
                    for a in expr.args:
                        _infer_expr(a, env, ctx, in_handler=in_handler)
                    return ANY_T
                seq_t = _infer_expr(expr.args[0], env, ctx, in_handler=in_handler)
                init_t = _infer_expr(expr.args[1], env, ctx, in_handler=in_handler)
                acc_name = expr.args[2]
                item_name = expr.args[3]
                if not isinstance(acc_name, NameExpr) or not isinstance(item_name, NameExpr):
                    ctx.err(f"{name} argument 3/4 must be identifier binders")
                    _infer_expr(expr.args[4], env, ctx, in_handler=in_handler)
                    return init_t
                if seq_t.kind == "list":
                    item_t = seq_t.elem or ANY_T
                else:
                    if seq_t.kind != "any":
                        ctx.err(f"{name} source must be list, got {type_text(seq_t)}")
                    item_t = ANY_T
                body_env = dict(env)
                body_env[acc_name.name] = init_t
                body_env[item_name.name] = item_t
                body_t = _infer_expr(expr.args[4], body_env, ctx, in_handler=in_handler)
                if not is_assignable(body_t, init_t):
                    ctx.err(
                        f"{name} reducer return mismatch: got {type_text(body_t)}, "
                        f"expected {type_text(init_t)}"
                    )
                return merge_types(init_t, body_t)

            if name in ctx.local_sigs:
                sig = ctx.local_sigs[name]
                if len(expr.args) != len(sig.params):
                    ctx.err(
                        f"call arity mismatch for '{name}': got {len(expr.args)}, expected {len(sig.params)}"
                    )
                for idx, arg in enumerate(expr.args):
                    arg_t = _infer_expr(arg, env, ctx, in_handler=in_handler)
                    if idx < len(sig.params):
                        _check_expect(ctx, arg_t, sig.params[idx], f"arg {idx + 1} of '{name}'")
                return sig.ret

            if name in BUILTINS:
                sig = BUILTINS[name]
                argc = len(expr.args)
                if argc < sig.min_args or (sig.max_args is not None and argc > sig.max_args):
                    exp = str(sig.min_args) if sig.max_args == sig.min_args else f"{sig.min_args}..{sig.max_args}"
                    ctx.err(f"call arity mismatch for builtin '{name}': got {argc}, expected {exp}")
                arg_ts = [_infer_expr(arg, env, ctx, in_handler=in_handler) for arg in expr.args]
                for idx in sig.numeric_args:
                    if idx < len(arg_ts):
                        _check_expect(ctx, arg_ts[idx], NUM_T, f"builtin '{name}' arg {idx + 1}")
                for idx in sig.string_args:
                    if idx < len(arg_ts):
                        _check_expect(ctx, arg_ts[idx], STR_T, f"builtin '{name}' arg {idx + 1}")
                for idx in sig.bool_args:
                    if idx < len(arg_ts):
                        _check_expect(ctx, arg_ts[idx], BOOL_T, f"builtin '{name}' arg {idx + 1}")
                return sig.ret

            # Unknown free callee is treated as external host call.
            for arg in expr.args:
                _infer_expr(arg, env, ctx, in_handler=in_handler)
            return ANY_T

        _infer_expr(expr.func, env, ctx, in_handler=in_handler)
        for arg in expr.args:
            _infer_expr(arg, env, ctx, in_handler=in_handler)
        return ANY_T

    if isinstance(expr, MemberExpr):
        if isinstance(expr.obj, NameExpr) and expr.obj.name == "self":
            if ctx.self_field_types and expr.name in ctx.self_field_types:
                return ctx.self_field_types[expr.name]
            if ctx.self_method_sigs and expr.name in ctx.self_method_sigs:
                return FUNC_T
            return ANY_T
        obj_t = _infer_expr(expr.obj, env, ctx, in_handler=in_handler)
        if obj_t.kind == "nominal" and ctx.class_shapes and obj_t.name in ctx.class_shapes:
            shape = ctx.class_shapes[obj_t.name]
            if expr.name in shape.field_types:
                return shape.field_types[expr.name]
            if expr.name in shape.method_sigs:
                return FUNC_T
            ctx.err(f"unknown member '{obj_t.name}.{expr.name}' in closed-shape class")
            return ANY_T
        if obj_t.kind == "record":
            fields = _record_fields(obj_t)
            if expr.name not in fields:
                ctx.err(f"member '{expr.name}' not found in record {type_text(obj_t)}")
                return ANY_T
            return fields[expr.name]
        if obj_t.kind in {"map", "any"}:
            return ANY_T
        ctx.err(f"member access on non-record/map type {type_text(obj_t)}")
        return ANY_T

    if isinstance(expr, IndexExpr):
        obj_t = _infer_expr(expr.obj, env, ctx, in_handler=in_handler)
        idx_t = _infer_expr(expr.index, env, ctx, in_handler=in_handler)
        _check_expect(ctx, idx_t, NUM_T, "index expression")
        idx_lit = _number_literal_value(expr.index)
        if idx_lit is not None and idx_lit >= 0 and int(idx_lit) == idx_lit:
            idx = int(idx_lit)
            if isinstance(expr.obj, ListExpr) and idx >= len(expr.obj.items):
                ctx.err(
                    f"index out of bounds for list literal: index={idx} len={len(expr.obj.items)}"
                )
            if isinstance(expr.obj, StringExpr):
                try:
                    lit_text = json.loads(expr.obj.value)
                except Exception:
                    lit_text = expr.obj.value.strip('"')
                if isinstance(lit_text, str) and idx >= len(lit_text):
                    ctx.err(
                        f"index out of bounds for string literal: index={idx} len={len(lit_text)}"
                    )
        if obj_t.kind == "list":
            return obj_t.elem or ANY_T
        if obj_t.kind == "str":
            return STR_T
        if obj_t.kind in {"any", "map", "record"}:
            return ANY_T
        ctx.err(f"indexing non-indexable type {type_text(obj_t)}")
        return ANY_T

    if isinstance(expr, SliceExpr):
        obj_t = _infer_expr(expr.obj, env, ctx, in_handler=in_handler)
        if expr.start is not None:
            _check_expect(
                ctx,
                _infer_expr(expr.start, env, ctx, in_handler=in_handler),
                NUM_T,
                "slice start",
            )
        if expr.end is not None:
            _check_expect(
                ctx,
                _infer_expr(expr.end, env, ctx, in_handler=in_handler),
                NUM_T,
                "slice end",
            )
        if obj_t.kind == "list":
            return obj_t
        if obj_t.kind == "str":
            return STR_T
        if obj_t.kind in {"any", "map", "record"}:
            return ANY_T
        ctx.err(f"slicing non-sliceable type {type_text(obj_t)}")
        return ANY_T

    if isinstance(expr, PatchExpr):
        base_t = _infer_expr(expr.obj, env, ctx, in_handler=in_handler)
        if base_t.kind == "record":
            fields = _record_fields(base_t)
            for it in expr.items:
                fields[it.key] = _infer_expr(it.value, env, ctx, in_handler=in_handler)
            return record_t(fields)
        for it in expr.items:
            _infer_expr(it.value, env, ctx, in_handler=in_handler)
        if base_t.kind in {"map", "any"}:
            return MAP_T
        ctx.err(f"patch target must be map/record, got {type_text(base_t)}")
        return ANY_T

    if isinstance(expr, MapBindExpr):
        base_t = _infer_expr(expr.base, env, ctx, in_handler=in_handler)
        if base_t.kind == "list":
            item_t = base_t.elem or ANY_T
        else:
            item_t = ANY_T
            if base_t.kind != "any":
                ctx.err(f"comprehension source must be list, got {type_text(base_t)}")
        env2 = dict(env)
        env2[expr.key] = item_t
        value_t = _infer_expr(expr.value, env2, ctx, in_handler=in_handler)
        return list_t(value_t)

    if isinstance(expr, RangeExpr):
        _check_expect(ctx, _infer_expr(expr.start, env, ctx, in_handler=in_handler), NUM_T, "range start")
        _check_expect(ctx, _infer_expr(expr.end, env, ctx, in_handler=in_handler), NUM_T, "range end")
        return list_t(NUM_T)

    if isinstance(expr, PropagateExpr):
        return _infer_expr(expr.expr, env, ctx, in_handler=in_handler)

    if isinstance(expr, ExceptionMatchExpr):
        _infer_expr(expr.exc, env, ctx, in_handler=in_handler)
        for t in expr.types:
            if isinstance(t, NameExpr):
                # Exception type names can be external host symbols.
                continue
            _infer_expr(t, env, ctx, in_handler=in_handler)
        return BOOL_T

    if isinstance(expr, ReraiseExpr):
        if not in_handler:
            ctx.err("reraise used outside try-catch handler")
        return NEVER_T

    if isinstance(expr, TryCatchExpr):
        body_t = _infer_expr(expr.body, env, ctx, in_handler=False)
        env2 = dict(env)
        env2[expr.err_name] = EXC_T
        handler_t = _infer_expr(expr.handler, env2, ctx, in_handler=True)
        return merge_types(body_t, handler_t)

    return ANY_T


def _build_local_signatures(program: Program) -> tuple[dict[str, FunctionSig], list[str]]:
    sigs: dict[str, FunctionSig] = {}
    errors: list[str] = []
    for decl in program.decls:
        if isinstance(decl, FuncDecl):
            name = decl.name
            params = tuple(type_from_ir(p.type_expr) for p in decl.params)
            ret = type_from_ir(decl.return_type)
        elif isinstance(decl, MethodDecl):
            name = f"{decl.class_name}__{decl.func_decl.name}"
            params = tuple(type_from_ir(p.type_expr) for p in decl.func_decl.params)
            if not decl.func_decl.params or decl.func_decl.params[0].name != "self":
                params = (ANY_T, *params)
            ret = type_from_ir(decl.func_decl.return_type)
        else:
            continue

        if name in sigs:
            errors.append(f"{program.module_name}: duplicate declaration '{name}'")
            continue
        sigs[name] = FunctionSig(params=params, ret=ret)
    return sigs, errors


def _check_param_uniqueness(module_name: str, fn_name: str, params: list[Param]) -> list[str]:
    seen: set[str] = set()
    errs: list[str] = []
    for p in params:
        if p.name in seen:
            errs.append(f"{module_name}:{fn_name}: duplicate parameter '{p.name}'")
        seen.add(p.name)
    return errs


def validate_program_semantics(program: Program) -> ProgramSemanticReport:
    local_sigs, top_errors = _build_local_signatures(program)
    class_shapes = _class_shapes(program)

    fn_reports: list[FunctionSemanticReport] = []
    all_errors: list[str] = list(top_errors)
    all_warnings: list[str] = []

    for decl in program.decls:
        if isinstance(decl, FuncDecl):
            report_name = decl.name
            fn_decl = decl
            errs = _check_param_uniqueness(program.module_name, report_name, fn_decl.params)
            warns: list[str] = []
            ctx = _FnCtx(
                module_name=program.module_name,
                fn_name=report_name,
                local_sigs=local_sigs,
                errors=errs,
                warnings=warns,
                class_shapes=class_shapes,
            )

            env: dict[str, StaticType] = {}
            for p in fn_decl.params:
                env[p.name] = type_from_ir(p.type_expr)

            body_t = _infer_expr(fn_decl.body, env, ctx, in_handler=False)
            ret_t = type_from_ir(fn_decl.return_type)
            if not is_assignable(body_t, ret_t):
                ctx.err(f"return type mismatch: got {type_text(body_t)}, expected {type_text(ret_t)}")

            fn_reports.append(
                FunctionSemanticReport(
                    name=report_name,
                    errors=tuple(ctx.errors),
                    warnings=tuple(ctx.warnings),
                )
            )
            all_errors.extend(ctx.errors)
            all_warnings.extend(ctx.warnings)
            continue

        if isinstance(decl, MethodDecl):
            report_name = f"{decl.class_name}__{decl.func_decl.name}"
            fn_decl = decl.func_decl
            errs = _check_param_uniqueness(program.module_name, report_name, fn_decl.params)
            if fn_decl.params and fn_decl.params[0].name == "self":
                errs.append(
                    f"{program.module_name}:{report_name}: receiver is implicit; remove explicit self parameter"
                )
            if decl.class_name not in class_shapes:
                errs.append(
                    f"{program.module_name}:{report_name}: method declared for unknown class '{decl.class_name}'"
                )
            warns = []
            ctx = _FnCtx(
                module_name=program.module_name,
                fn_name=report_name,
                local_sigs=local_sigs,
                errors=errs,
                warnings=warns,
                class_shapes=class_shapes,
            )

            shape = class_shapes.get(
                decl.class_name,
                _ClassShape(fields=set(), methods=set(), field_types={}, method_sigs={}),
            )
            class_fields = shape.fields
            class_methods = shape.methods
            allowed_members = set(class_fields) | set(class_methods)
            for ref in _iter_self_member_refs(fn_decl.body):
                if ref not in allowed_members:
                    ctx.err(
                        f"unknown self member '{ref}' in closed-shape class '{decl.class_name}'"
                    )
            for key in _iter_self_mutation_keys(fn_decl.body):
                if key not in class_fields:
                    ctx.err(
                        f"invalid self mutation of unknown field '{key}' in closed-shape class '{decl.class_name}'"
                    )

            env = {"self": ANY_T}
            for p in fn_decl.params:
                env[p.name] = type_from_ir(p.type_expr)
            ctx.self_field_types = shape.field_types
            ctx.self_method_sigs = shape.method_sigs
            body_t = _infer_expr(fn_decl.body, env, ctx, in_handler=False)
            ret_t = type_from_ir(fn_decl.return_type)
            if not is_assignable(body_t, ret_t):
                ctx.err(f"return type mismatch: got {type_text(body_t)}, expected {type_text(ret_t)}")

            fn_reports.append(
                FunctionSemanticReport(
                    name=report_name,
                    errors=tuple(ctx.errors),
                    warnings=tuple(ctx.warnings),
                )
            )
            all_errors.extend(ctx.errors)
            all_warnings.extend(ctx.warnings)
            continue

        if isinstance(decl, ClassDecl):
            report_name = decl.name
            errs = _check_param_uniqueness(program.module_name, report_name, decl.params)
            warns = []
            ctx = _FnCtx(
                module_name=program.module_name,
                fn_name=report_name,
                local_sigs=local_sigs,
                errors=errs,
                warnings=warns,
                class_shapes=class_shapes,
            )

            env = {p.name: type_from_ir(p.type_expr) for p in decl.params}
            shape = class_shapes.get(decl.name)
            if shape is None:
                shape = _ClassShape(fields=set(), methods=set(), field_types={}, method_sigs={})
                class_shapes[decl.name] = shape

            header_fields = {p.name for p in decl.params}
            shape.fields = set(header_fields)
            shape.field_types = dict(env)

            if isinstance(decl.body, MapExpr):
                seen = set(header_fields)
                seen_defaults: set[str] = set()
                seen_types: dict[str, StaticType] = dict(env)
                for item in decl.body.items:
                    key = _normalized_item_key(item.key, item.key_is_string)
                    if key in header_fields:
                        ctx.err(f"class field '{key}' duplicates header parameter")
                    if key in seen_defaults:
                        ctx.err(f"duplicate class field initializer '{key}'")
                    refs = _iter_self_member_refs(item.value)
                    for ref in refs:
                        if ref not in seen:
                            ctx.err(
                                f"class field '{key}' initializer references '{ref}' before initialization"
                            )

                    ctx.self_field_types = dict(seen_types)
                    ctx.self_method_sigs = dict(shape.method_sigs)
                    value_t = _infer_expr(item.value, env, ctx, in_handler=False)

                    if key not in header_fields and key not in seen_defaults:
                        seen_defaults.add(key)
                        seen.add(key)
                        seen_types[key] = value_t
                    elif key not in header_fields:
                        seen.add(key)
                shape.fields = seen
                shape.field_types = seen_types
                body_t = record_t(seen_types)
            else:
                ctx.self_field_types = dict(shape.field_types)
                ctx.self_method_sigs = dict(shape.method_sigs)
                body_t = _infer_expr(decl.body, env, ctx, in_handler=False)

            ctx.self_field_types = None
            ctx.self_method_sigs = None
            if body_t.kind not in {"record", "map", "any"}:
                ctx.err(
                    "class body must evaluate to map/record defaults, "
                    f"got {type_text(body_t)}"
                )

            fn_reports.append(
                FunctionSemanticReport(
                    name=report_name,
                    errors=tuple(ctx.errors),
                    warnings=tuple(ctx.warnings),
                )
            )
            all_errors.extend(ctx.errors)
            all_warnings.extend(ctx.warnings)
            continue

        all_errors.append(
            f"{program.module_name}: unsupported declaration type {type(decl).__name__}"
        )

    return ProgramSemanticReport(
        module_name=program.module_name,
        functions=tuple(fn_reports),
        errors=tuple(all_errors),
        warnings=tuple(all_warnings),
    )


def _validate_paths(paths: list[Path], max_warnings: int) -> tuple[int, int]:
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
            report = validate_program_semantics(program)
            total_modules += 1
            total_functions += len(report.functions)

            for msg in report.warnings:
                total_warnings += 1
                print(f"warning: {msg}")
            for msg in report.errors:
                total_errors += 1
                print(f"error: {msg}")

    print(
        "semantic_validation_summary: "
        f"modules={total_modules} functions={total_functions} "
        f"warnings={total_warnings} errors={total_errors}"
    )
    if total_errors:
        return 1, total_warnings
    if max_warnings >= 0 and total_warnings > max_warnings:
        print(
            "semantic_validation_gate_fail: "
            f"warnings={total_warnings} > max_warnings={max_warnings}"
        )
        return 1, total_warnings
    return 0, total_warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond static semantics.")
    ap.add_argument(
        "--in",
        dest="inputs",
        action="append",
        required=True,
        help="Input .dmd file or directory (repeatable)",
    )
    ap.add_argument(
        "--max-warnings",
        type=int,
        default=-1,
        help="Fail if warnings exceed this count (-1 disables warning cap)",
    )
    args = ap.parse_args(argv)

    paths = [Path(p) for p in args.inputs]
    code, _ = _validate_paths(paths, max_warnings=args.max_warnings)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
