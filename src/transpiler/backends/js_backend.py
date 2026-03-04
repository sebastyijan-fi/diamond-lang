"""JavaScript backend emitter (executable JS codegen)."""

from __future__ import annotations

from diamond_ir import (
    BinaryExpr,
    BoolExpr,
    CallExpr,
    CapabilityCheckOp,
    ClassDecl,
    ErrorContextOp,
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
    PatternIdent,
    PatternLiteral,
    PatternWild,
    PropagateExpr,
    Program,
    RangeExpr,
    ReraiseExpr,
    ResourceIncrementOp,
    SequenceExpr,
    SliceExpr,
    StringExpr,
    TernaryExpr,
    ToolOp,
    TraceEntryOp,
    TraceExitOp,
    TryCatchExpr,
    TypeExpr,
    TypeName,
    TypeList,
    TypeRecord,
    UnaryExpr,
)
from ir_format import type_to_text

EXT = ".js"

_CONTROL_TOOLS = {"c", "t", "b", "e"}

_CALL_MAP = {
    "ext": "dm.extern_call",
    "ln": "dm.len",
    "trim": "dm.trim",
    "split": "dm.split",
    "peek": "dm.peek",
    "take": "dm.take",
    "gd": "dm.guard",
    "put": "dm.put",
    "get": "dm.get",
    "del": "dm.del",
    "jenc": "dm.json_dumps",
    "jdec": "dm.json_loads",
    "S": "dm.to_s",
    "I": "dm.to_i",
    "B": "dm.to_b",
    "O": "dm.to_o",
    "l": "dm.left_half",
    "r": "dm.right_half",
    "cw": "dm.call_with",
    "slp": "dm.sleep",
    "rnd": "dm.rand_uniform",
    "is_tup": "dm.is_tuple",
    "logw": "dm.log_retry_warning",
    "mk_retry": "dm.make_retry_decorator",
    "q": "dm.ini_repr",
    "pair": "dm.ini_pair",
    "splitln": "dm.ini_splitlines_keepends",
    "ini_raise": "dm.ini_raise",
    "ini_iscommentline": "dm.ini_iscommentline",
    "ini_parseline": "dm.ini_parseline",
    "ini_parse_lines": "dm.ini_parse_lines",
    "ini_parse_ini_data": "dm.ini_parse_ini_data",
    "mgrp": "dm.re_group",
    "pad6": "dm.pad6",
    "ibase": "dm.parse_int_base",
    "dtd": "dm.dt_date",
    "dtt": "dm.dt_datetime",
    "dttm": "dm.dt_time",
    "tzutc": "dm.tz_utc",
    "tzoff": "dm.tz_offset",
}


def _has_tool(decl: FuncDecl, tool_type: type) -> bool:
    return any(isinstance(op, tool_type) for op in decl.tool_ops)


def _map_key_text(key: str) -> str:
    return repr(key)


def _method_name(class_name: str, method_name: str) -> str:
    return f"{class_name}__{method_name}"


def _emit_pattern(pattern: PatternWild | PatternIdent | PatternLiteral, env: set[str]) -> tuple[str, str | None]:
    if isinstance(pattern, PatternWild):
        return "dm.WILD", None
    if isinstance(pattern, PatternIdent):
        if pattern.name in env:
            return pattern.name, None
        return f"dm.capture({pattern.name!r})", pattern.name
    if isinstance(pattern, PatternLiteral):
        return _emit_expr(pattern.literal, env), None
    raise ValueError(f"unsupported pattern: {pattern}")


def _emit_expr(expr: Expr, env: set[str], *, in_handler: bool = False) -> str:
    if isinstance(expr, NameExpr):
        if expr.name in env:
            return expr.name
        if expr.name == "t":
            return "true"
        if expr.name == "f":
            return "false"
        if expr.name == "none":
            return "null"
        return expr.name

    if isinstance(expr, NumberExpr):
        return expr.value
    if isinstance(expr, StringExpr):
        return expr.value
    if isinstance(expr, BoolExpr):
        return "true" if expr.value else "false"

    if isinstance(expr, ListExpr):
        return "[" + ", ".join(_emit_expr(x, env, in_handler=in_handler) for x in expr.items) + "]"

    if isinstance(expr, MapExpr):
        items = ", ".join(f"{_map_key_text(it.key)}: {_emit_expr(it.value, env, in_handler=in_handler)}" for it in expr.items)
        return "{" + items + "}"

    if isinstance(expr, UnaryExpr):
        if expr.op == "-":
            return f"(-{_emit_expr(expr.expr, env, in_handler=in_handler)})"
        raise ValueError(f"unsupported unary op: {expr.op}")

    if isinstance(expr, BinaryExpr):
        left = _emit_expr(expr.left, env, in_handler=in_handler)
        right = _emit_expr(expr.right, env, in_handler=in_handler)
        if expr.op == "/":
            return f"dm.idiv({left}, {right})"
        if expr.op == "$":
            return f"dm.midpoint({left}, {right})"
        if expr.op == "^":
            return f"dm.pow({left}, {right})"
        if expr.op == "&":
            return f"(dm.isTruthy({left}) && dm.isTruthy({right}))"
        if expr.op == "|":
            return f"(dm.isTruthy({left}) || dm.isTruthy({right}))"
        if expr.op in {"+", "-", "*", "%", "==", "!=", "<", "<=", ">", ">="}:
            return f"dm.binop({repr(expr.op)}, {left}, {right})"
        raise ValueError(f"unsupported binary op: {expr.op}")

    if isinstance(expr, TernaryExpr):
        cond = _emit_expr(expr.cond, env, in_handler=in_handler)
        yes = _emit_expr(expr.then_expr, env, in_handler=in_handler)
        no = _emit_expr(expr.else_expr, env, in_handler=in_handler)
        return f"(dm.isTruthy({cond}) ? {yes} : {no})"

    if isinstance(expr, SequenceExpr):
        parts = ", ".join(
            f"() => {_emit_expr(item, env, in_handler=in_handler)}" for item in expr.items
        )
        return f"dm.seq([{parts}])"

    if isinstance(expr, MatchExpr):
        subject = _emit_expr(expr.subject, env, in_handler=in_handler)
        arms: list[str] = []
        for arm in expr.arms:
            pat, capture_name = _emit_pattern(arm.pattern, env)
            arm_env = set(env)
            if capture_name is not None:
                arm_env.add(capture_name)
                expr_code = _emit_expr(arm.expr, arm_env, in_handler=in_handler)
                arms.append(f"[{pat}, ({capture_name}) => {expr_code}]")
            else:
                expr_code = _emit_expr(arm.expr, arm_env, in_handler=in_handler)
                arms.append(f"[{pat}, () => {expr_code}]")
        return f"dm.match({subject}, [{', '.join(arms)}])"

    if isinstance(expr, CallExpr):
        if isinstance(expr.func, MemberExpr):
            recv = _emit_expr(expr.func.obj, env, in_handler=in_handler)
            args = ", ".join(_emit_expr(a, env, in_handler=in_handler) for a in expr.args)
            return f"dm.obj_invoke(__dm_scope, {recv}, {expr.func.name!r}, [{args}])"

        if isinstance(expr.func, NameExpr):
            name = expr.func.name
            args = [_emit_expr(a, env, in_handler=in_handler) for a in expr.args]
            if (name in {"fd", "fold"}) and len(expr.args) == 5:
                base = args[0]
                init = args[1]
                acc = args[2]
                item = args[3]
                body_env = set(env)
                if acc.isidentifier():
                    body_env.add(acc)
                if item.isidentifier():
                    body_env.add(item)
                body = _emit_expr(expr.args[4], body_env, in_handler=in_handler)
                return f"dm.fold({base}, {init}, ({acc}, {item}) => {body})"
            callee = _CALL_MAP.get(name, f"dm.{name}")
            return f"{callee}({', '.join(args)})"

        callee = _emit_expr(expr.func, env, in_handler=in_handler)
        args = ", ".join(_emit_expr(a, env, in_handler=in_handler) for a in expr.args)
        return f"{callee}({args})"

    if isinstance(expr, MemberExpr):
        if isinstance(expr.obj, NameExpr) and expr.obj.name == "self":
            return f"dm.obj_get(self, {expr.name!r})"
        return f"dm.member({_emit_expr(expr.obj, env, in_handler=in_handler)}, '{expr.name}')"

    if isinstance(expr, IndexExpr):
        return f"dm.index({_emit_expr(expr.obj, env, in_handler=in_handler)}, {_emit_expr(expr.index, env, in_handler=in_handler)})"

    if isinstance(expr, SliceExpr):
        start = _emit_expr(expr.start, env, in_handler=in_handler) if expr.start is not None else "undefined"
        end = _emit_expr(expr.end, env, in_handler=in_handler) if expr.end is not None else "undefined"
        return f"dm.slice({_emit_expr(expr.obj, env, in_handler=in_handler)}, {start}, {end})"

    if isinstance(expr, PatchExpr):
        updates = ", ".join(
            f"{_map_key_text(item.key)}: {_emit_expr(item.value, env, in_handler=in_handler)}"
            for item in expr.items
        )
        return f"dm.patch({_emit_expr(expr.obj, env, in_handler=in_handler)}, {{{updates}}})"

    if isinstance(expr, MapBindExpr):
        body = _emit_expr(expr.value, env | {expr.key}, in_handler=in_handler)
        return f"dm.mapBind({_emit_expr(expr.base, env, in_handler=in_handler)}, ({expr.key}) => {body})"

    if isinstance(expr, RangeExpr):
        return f"dm.rangeInclusive({_emit_expr(expr.start, env, in_handler=in_handler)}, {_emit_expr(expr.end, env, in_handler=in_handler)})"

    if isinstance(expr, PropagateExpr):
        return f"dm.propagate(() => {_emit_expr(expr.expr, env, in_handler=in_handler)})"

    if isinstance(expr, ExceptionMatchExpr):
        subject = _emit_expr(expr.exc, env, in_handler=in_handler)
        types = ", ".join(_emit_expr(t, env, in_handler=in_handler) for t in expr.types)
        return f"dm.isException({_emit_expr(expr.exc, env, in_handler=in_handler)}, [{types}])"

    if isinstance(expr, ReraiseExpr):
        if not in_handler:
            raise ValueError("reraise is only valid inside a handler")
        return "dm.RERAISE"

    if isinstance(expr, TryCatchExpr):
        body = _emit_expr(expr.body, env, in_handler=False)
        handler_expr = _emit_expr(
            expr.handler,
            env | {expr.err_name},
            in_handler=True,
        )
        return f"dm.tryCatch(() => {body}, ({expr.err_name}) => ({handler_expr}))"

    raise ValueError(f"unsupported expr: {expr}")


def _emit_named_func(decl: FuncDecl, emit_name: str, doc_extra: str = "") -> list[str]:
    lines: list[str] = []
    tools = ",".join(decl.tools) if decl.tools else "-"
    ret = type_to_text(decl.return_type)
    sig = ", ".join(p.name for p in decl.params)
    env = {p.name for p in decl.params}
    lines.append(f"export function {emit_name}({sig}) {{")
    lines.append(f"  // tools: {tools}")
    lines.append(f"  // ret: {ret}")
    if doc_extra:
        lines.append(f"  // {doc_extra}")
    if _has_tool(decl, CapabilityCheckOp):
        lines.append(f"  dm.capCheck('{emit_name}', [{', '.join(repr(t) for t in decl.tools if t not in _CONTROL_TOOLS)}])")
    if _has_tool(decl, ResourceIncrementOp):
        lines.append("  dm.resourceTick('steps')")
    if _has_tool(decl, TraceEntryOp):
        lines.append(f"  dm.traceEnter('{emit_name}', [{sig}])")

    body = _emit_expr(decl.body, env)
    if _has_tool(decl, ErrorContextOp):
        lines.append("  try {")
        lines.append(f"    const __result = {body};")
        if _has_tool(decl, TraceExitOp):
            lines.append(f"    dm.traceExit('{emit_name}', __result)")
        lines.append("    return __result;")
        lines.append("  } catch (err) {")
        lines.append(f"    throw dm.withErrorContext(err, '{emit_name}')")
        lines.append("  }")
    else:
        lines.append(f"  const __result = {body};")
        if _has_tool(decl, TraceExitOp):
            lines.append(f"  dm.traceExit('{emit_name}', __result)")
        lines.append("  return __result;")

    lines.append("}")
    lines.append("")
    return lines


def _emit_func(decl: FuncDecl) -> list[str]:
    return _emit_named_func(decl, decl.name)


def _emit_method(decl: MethodDecl) -> list[str]:
    emit_name = _method_name(decl.class_name, decl.func_decl.name)
    params = decl.func_decl.params
    if not params or params[0].name != "self":
        params = [Param(name="self", type_expr=TypeName(name="O")), *params]
    method_decl = FuncDecl(
        name=decl.func_decl.name,
        params=params,
        return_type=decl.func_decl.return_type,
        body=decl.func_decl.body,
        tools=decl.func_decl.tools,
        tool_ops=decl.func_decl.tool_ops,
    )
    return _emit_named_func(
        method_decl,
        emit_name,
        doc_extra=f"method:{decl.class_name}.{decl.func_decl.name}",
    )


def _emit_class_ctor(decl: ClassDecl) -> list[str]:
    lines: list[str] = []
    sig = ", ".join(p.name for p in decl.params)
    env = {p.name for p in decl.params}
    header_items = ", ".join(f"{repr(p.name)}: {p.name}" for p in decl.params)
    header_map = "{" + header_items + "}" if header_items else "{}"

    lines.append(f"export function {decl.name}({sig}) {{")
    lines.append("  // class ctor")
    lines.append(f"  const __dm_fields = {header_map};")

    if isinstance(decl.body, MapExpr):
        for item in decl.body.items:
            key = _map_key_text(item.key)
            lines.append(f"  if (Object.prototype.hasOwnProperty.call(__dm_fields, {key})) {{")
            lines.append(f"    throw new Error('duplicate field initializer: {item.key}');")
            lines.append("  }")
            lines.append(f"  __dm_fields[{key}] = null;")
        lines.append(f"  const __dm_obj = dm.obj_new(__dm_fields, {decl.name!r});")
        lines.append("  const self = __dm_obj;")
        for item in decl.body.items:
            key = _map_key_text(item.key)
            value = _emit_expr(item.value, env | {"self"})
            lines.append(f"  dm.obj_set(__dm_obj, {key}, {value});")
    else:
        defaults_expr = _emit_expr(decl.body, env)
        lines.append(f"  const __dm_defaults = {defaults_expr};")
        lines.append("  if (!__dm_defaults || typeof __dm_defaults !== 'object' || Array.isArray(__dm_defaults)) {")
        lines.append("    throw new Error('class body must evaluate to map/record defaults');")
        lines.append("  }")
        lines.append("  for (const __k of Object.keys(__dm_defaults)) {")
        lines.append("    if (Object.prototype.hasOwnProperty.call(__dm_fields, __k)) {")
        lines.append("      throw new Error(`duplicate field initializer: ${__k}`);")
        lines.append("    }")
        lines.append("    __dm_fields[__k] = null;")
        lines.append("  }")
        lines.append(f"  const __dm_obj = dm.obj_new(__dm_fields, {decl.name!r});")
        lines.append("  const self = __dm_obj;")
        lines.append("  for (const [__k, __v] of Object.entries(__dm_defaults)) {")
        lines.append("    dm.obj_set(__dm_obj, __k, __v);")
        lines.append("  }")

    lines.append("  return __dm_obj;")
    lines.append("}")
    lines.append("")
    return lines


def emit(program: Program) -> str:
    lines: list[str] = []
    exported_names: list[str] = []
    lines.append("// Auto-generated from Diamond IR (JS backend, executable mode)")
    lines.append("import * as dm from './diamond_runtime.js';")
    lines.append("")
    lines.append(f"// source_module: {program.module_name}")
    lines.append("")

    for d in program.decls:
        if isinstance(d, FuncDecl):
            lines.extend(_emit_func(d))
            exported_names.append(d.name)
            continue
        if isinstance(d, ClassDecl):
            lines.extend(_emit_class_ctor(d))
            exported_names.append(d.name)
            continue
        if isinstance(d, MethodDecl):
            name = _method_name(d.class_name, d.func_decl.name)
            lines.extend(_emit_method(d))
            exported_names.append(name)
            continue
        raise ValueError(f"unsupported top-level declaration: {type(d).__name__}")

    lines.append("const __dm_scope = Object.create(null);")
    for name in exported_names:
        lines.append(f"__dm_scope[{name!r}] = {name};")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"
