"""Python backend emitter (v0 correctness target)."""

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
    TraceEntryOp,
    TraceExitOp,
    TryCatchExpr,
    TypeName,
    UnaryExpr,
)
from ir_format import type_to_text

EXT = ".py"

_CALL_MAP: dict[str, str] = {
    "ext": "dm.extern_call",
    "ln": "dm.ln",
    "trim": "dm.trim",
    "split": "dm.split",
    "peek": "dm.peek",
    "take": "dm.take",
    "gd": "dm.guard",
    "put": "dm.put",
    "get": "dm.get",
    "del": "dm.del_",
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


def _map_key_text(key: str, is_string: bool) -> str:
    return key if is_string else repr(key)


def _method_name(class_name: str, method_name: str) -> str:
    return f"{class_name}__{method_name}"


def _emit_pattern(
    pattern: PatternWild | PatternIdent | PatternLiteral, env: set[str]
) -> tuple[str, str | None]:
    if isinstance(pattern, PatternWild):
        return "dm.WILD", None
    if isinstance(pattern, PatternIdent):
        if pattern.name in env:
            return pattern.name, None
        return f"dm.CAPTURE({pattern.name!r})", pattern.name
    if isinstance(pattern, PatternLiteral):
        return _emit_expr(pattern.literal, env), None
    raise ValueError(f"unsupported pattern: {pattern}")


def _emit_expr(expr: Expr, env: set[str], in_handler: bool = False) -> str:
    if isinstance(expr, NameExpr):
        if expr.name in env:
            return expr.name
        if expr.name == "t":
            return "True"
        if expr.name == "f":
            return "False"
        if expr.name == "none":
            return "None"
        return expr.name

    if isinstance(expr, NumberExpr):
        return expr.value
    if isinstance(expr, StringExpr):
        return expr.value
    if isinstance(expr, BoolExpr):
        return "True" if expr.value else "False"

    if isinstance(expr, ListExpr):
        return "[" + ", ".join(_emit_expr(x, env) for x in expr.items) + "]"

    if isinstance(expr, MapExpr):
        items = ", ".join(f"{_map_key_text(it.key, it.key_is_string)}: {_emit_expr(it.value, env)}" for it in expr.items)
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
            return f"({left} ** {right})"
        if expr.op == "&":
            return f"({left} and {right})"
        if expr.op == "|":
            return f"({left} or {right})"
        if expr.op in {"+", "-", "*", "%", "==", "!=", "<", "<=", ">", ">="}:
            return f"({left} {expr.op} {right})"
        raise ValueError(f"unsupported binary op: {expr.op}")

    if isinstance(expr, TernaryExpr):
        cond = _emit_expr(expr.cond, env, in_handler=in_handler)
        yes = _emit_expr(expr.then_expr, env, in_handler=in_handler)
        no = _emit_expr(expr.else_expr, env, in_handler=in_handler)
        return f"({yes} if {cond} else {no})"

    if isinstance(expr, SequenceExpr):
        parts = ", ".join(f"(lambda: {_emit_expr(it, env, in_handler=in_handler)})" for it in expr.items)
        return f"dm.seq([{parts}])"

    if isinstance(expr, MatchExpr):
        subj = _emit_expr(expr.subject, env, in_handler=in_handler)
        arms: list[str] = []
        for arm in expr.arms:
            pat_expr, capture_name = _emit_pattern(arm.pattern, env)
            arm_env = set(env)
            if capture_name is not None:
                arm_env.add(capture_name)
                arm_expr = _emit_expr(arm.expr, arm_env, in_handler=in_handler)
                arm_thunk = f"lambda {capture_name}: {arm_expr}"
            else:
                arm_expr = _emit_expr(arm.expr, arm_env, in_handler=in_handler)
                arm_thunk = f"lambda: {arm_expr}"
            arms.append(f"({pat_expr}, {arm_thunk})")
        arms_text = ", ".join(arms)
        return f"dm.match({subj}, [{arms_text}])"

    if isinstance(expr, CallExpr):
        if isinstance(expr.func, MemberExpr):
            recv = _emit_expr(expr.func.obj, env, in_handler=in_handler)
            argv = ", ".join(_emit_expr(a, env, in_handler=in_handler) for a in expr.args)
            return f"dm.obj_invoke(globals(), {recv}, {expr.func.name!r}, [{argv}])"

        if isinstance(expr.func, NameExpr):
            name = expr.func.name
            if name in {"fold", "fd"} and len(expr.args) == 5:
                acc_expr = expr.args[2]
                item_expr = expr.args[3]
                if isinstance(acc_expr, NameExpr) and isinstance(item_expr, NameExpr):
                    seq = _emit_expr(expr.args[0], env, in_handler=in_handler)
                    init = _emit_expr(expr.args[1], env, in_handler=in_handler)
                    acc = acc_expr.name
                    item = item_expr.name
                    body = _emit_expr(expr.args[4], env | {acc, item}, in_handler=in_handler)
                    return f"dm.fold({seq}, {init}, lambda {acc}, {item}: {body})"
            callee = _CALL_MAP.get(name, name)
            args = ", ".join(_emit_expr(a, env, in_handler=in_handler) for a in expr.args)
            return f"{callee}({args})"

        callee = _emit_expr(expr.func, env, in_handler=in_handler)
        args = ", ".join(_emit_expr(a, env, in_handler=in_handler) for a in expr.args)
        return f"{callee}({args})"

    if isinstance(expr, MemberExpr):
        if isinstance(expr.obj, NameExpr) and expr.obj.name == "self":
            return f"dm.obj_get(self, {expr.name!r})"
        return f"dm.member({_emit_expr(expr.obj, env, in_handler=in_handler)}, {expr.name!r})"

    if isinstance(expr, IndexExpr):
        return f"{_emit_expr(expr.obj, env, in_handler=in_handler)}[{_emit_expr(expr.index, env, in_handler=in_handler)}]"

    if isinstance(expr, SliceExpr):
        start = _emit_expr(expr.start, env, in_handler=in_handler) if expr.start is not None else ""
        end = _emit_expr(expr.end, env, in_handler=in_handler) if expr.end is not None else ""
        return f"{_emit_expr(expr.obj, env, in_handler=in_handler)}[{start}:{end}]"

    if isinstance(expr, PatchExpr):
        updates = ", ".join(
            f"{_map_key_text(it.key, it.key_is_string)}: {_emit_expr(it.value, env, in_handler=in_handler)}"
            for it in expr.items
        )
        return f"dm.patch({_emit_expr(expr.obj, env, in_handler=in_handler)}, {{{updates}}})"

    if isinstance(expr, MapBindExpr):
        src = _emit_expr(expr.base, env, in_handler=in_handler)
        body = _emit_expr(expr.value, env | {expr.key}, in_handler=in_handler)
        return f"[{body} for {expr.key} in {src}]"

    if isinstance(expr, RangeExpr):
        return f"dm.range_inclusive({_emit_expr(expr.start, env, in_handler=in_handler)}, {_emit_expr(expr.end, env, in_handler=in_handler)})"

    if isinstance(expr, PropagateExpr):
        return f"dm.propagate(lambda: {_emit_expr(expr.expr, env, in_handler=in_handler)})"

    if isinstance(expr, ExceptionMatchExpr):
        err = _emit_expr(expr.exc, env, in_handler=in_handler)
        parts = [_emit_expr(t, env, in_handler=in_handler) for t in expr.types]
        if len(parts) == 1:
            return f"isinstance({err}, {parts[0]})"
        return f"isinstance({err}, ({', '.join(parts)}))"

    if isinstance(expr, ReraiseExpr):
        if not in_handler:
            raise ValueError("reraise is only valid inside an error handler")
        return "dm.RERAISE"

    if isinstance(expr, TryCatchExpr):
        body = _emit_expr(expr.body, env, in_handler=False)
        handler = _emit_expr(expr.handler, env | {expr.err_name}, in_handler=True)
        return f"dm.try_catch(lambda: {body}, lambda {expr.err_name}: {handler})"

    raise ValueError(f"unsupported expr: {expr}")


def _emit_named_func(decl: FuncDecl, emit_name: str, doc_extra: str = "") -> list[str]:
    lines: list[str] = []
    sig = ", ".join(p.name for p in decl.params)
    tools = ",".join(decl.tools) if decl.tools else "-"
    ret = type_to_text(decl.return_type)
    env = {p.name for p in decl.params}
    body = _emit_expr(decl.body, env)

    args_tuple = "(" + ", ".join(p.name for p in decl.params)
    if len(decl.params) == 1:
        args_tuple += ","
    args_tuple += ")"

    lines.append(f"def {emit_name}({sig}):")
    doc = f"ret:{ret} tools:{tools}"
    if doc_extra:
        doc += f" {doc_extra}"
    lines.append(f"    \"\"\"{doc}\"\"\"")

    if _has_tool(decl, CapabilityCheckOp):
        lines.append(f"    dm.cap_check({emit_name!r}, {decl.tools!r})")
    if _has_tool(decl, ResourceIncrementOp):
        lines.append(f"    dm.resource_tick({emit_name!r})")
    if _has_tool(decl, TraceEntryOp):
        lines.append(f"    dm.trace_enter({emit_name!r}, {args_tuple})")

    if _has_tool(decl, ErrorContextOp):
        lines.append("    try:")
        lines.append(f"        _dm_result = {body}")
        if _has_tool(decl, TraceExitOp):
            lines.append(f"        dm.trace_exit({emit_name!r}, _dm_result)")
        lines.append("        return _dm_result")
        lines.append("    except Exception as exc:")
        lines.append(f"        raise dm.with_error_context(exc, {emit_name!r})")
    else:
        lines.append(f"    _dm_result = {body}")
        if _has_tool(decl, TraceExitOp):
            lines.append(f"    dm.trace_exit({emit_name!r}, _dm_result)")
        lines.append("    return _dm_result")

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
    header_items = ", ".join(f"{p.name!r}: {p.name}" for p in decl.params)
    header_map = "{" + header_items + "}" if header_items else "{}"

    lines.append(f"def {decl.name}({sig}):")
    lines.append("    \"\"\"class ctor\"\"\"")
    lines.append(f"    _dm_fields = {header_map}")

    if isinstance(decl.body, MapExpr):
        for item in decl.body.items:
            key = _map_key_text(item.key, item.key_is_string)
            lines.append(f"    if {key} in _dm_fields:")
            lines.append(f"        raise AttributeError('duplicate field initializer: {item.key}')")
            lines.append(f"    _dm_fields[{key}] = None")
        lines.append(f"    _dm_obj = dm.obj_new(_dm_fields, class_name={decl.name!r})")
        lines.append("    self = _dm_obj")
        for item in decl.body.items:
            key = _map_key_text(item.key, item.key_is_string)
            value = _emit_expr(item.value, env | {"self"})
            lines.append(f"    dm.obj_set(_dm_obj, {key}, {value})")
    else:
        defaults_expr = _emit_expr(decl.body, env)
        lines.append(f"    _dm_defaults = {defaults_expr}")
        lines.append("    if not isinstance(_dm_defaults, dict):")
        lines.append(
            "        raise TypeError(\"class body must evaluate to map/record defaults\")"
        )
        lines.append("    for _k in _dm_defaults.keys():")
        lines.append("        if _k in _dm_fields:")
        lines.append("            raise AttributeError(f\"duplicate field initializer: {_k}\")")
        lines.append("        _dm_fields[_k] = None")
        lines.append(f"    _dm_obj = dm.obj_new(_dm_fields, class_name={decl.name!r})")
        lines.append("    self = _dm_obj")
        lines.append("    for _k, _v in _dm_defaults.items():")
        lines.append("        dm.obj_set(_dm_obj, _k, _v)")

    lines.append("    return _dm_obj")
    lines.append("")
    return lines


def emit(program: Program) -> str:
    lines: list[str] = []
    lines.append('"""Auto-generated from Diamond IR (Python backend, executable mode)."""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("import diamond_runtime as dm")
    lines.append("")
    lines.append(f"# source_module: {program.module_name}")
    lines.append("")

    for d in program.decls:
        if isinstance(d, FuncDecl):
            lines.extend(_emit_func(d))
            continue
        if isinstance(d, ClassDecl):
            lines.extend(_emit_class_ctor(d))
            continue
        if isinstance(d, MethodDecl):
            lines.extend(_emit_method(d))
            continue
        raise ValueError(f"unsupported top-level declaration: {type(d).__name__}")

    return "\n".join(lines).rstrip() + "\n"
