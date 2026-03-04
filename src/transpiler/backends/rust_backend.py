"""Rust backend emitter (executable mode)."""

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
    MapItem,
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

EXT = ".rs"

_CONTROL_TOOLS = {"c", "t", "b", "e"}

_CALL_MAP = {
    "ext": "extern_call",
    "ln": "len",
    "trim": "trim",
    "split": "split",
    "peek": "peek",
    "take": "take",
    "gd": "guard",
    "put": "put",
    "get": "get",
    "del": "del_",
    "jenc": "json_dumps",
    "jdec": "json_loads",
    "S": "to_s",
    "I": "to_i",
    "B": "to_b",
    "O": "to_o",
    "l": "left_half",
    "r": "right_half",
    "cw": "call_with",
    "slp": "sleep",
    "rnd": "rand_uniform",
    "is_tup": "is_tuple",
    "logw": "log_retry_warning",
    "mk_retry": "make_retry_decorator",
    "q": "ini_repr",
    "pair": "ini_pair",
    "splitln": "ini_splitlines_keepends",
    "ini_raise": "ini_raise",
    "ini_iscommentline": "ini_iscommentline",
    "ini_parseline": "ini_parseline",
    "ini_parse_lines": "ini_parse_lines",
    "ini_parse_ini_data": "ini_parse_ini_data",
    "mgrp": "re_group",
    "pad6": "pad6",
    "ibase": "parse_int_base",
    "dtd": "dt_date",
    "dtt": "dt_datetime",
    "dttm": "dt_time",
    "tzutc": "tz_utc",
    "tzoff": "tz_offset",
}


def _has_tool(decl: FuncDecl, tool_type: type) -> bool:
    return any(isinstance(op, tool_type) for op in decl.tool_ops)


def _map_type(_t: str) -> str:
    # Emit broad Value-based signatures for runtime compatibility across all constructs.
    return "serde_json::Value"


def _emit_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _map_key_text(key: str) -> str:
    return f'"{_emit_literal(key)}"'


def _method_name(class_name: str, method_name: str) -> str:
    return f"{class_name}__{method_name}"


def _emit_pattern(
    pattern: PatternWild | PatternIdent | PatternLiteral, env: set[str], func_names: set[str]
) -> tuple[str, str | None]:
    if isinstance(pattern, PatternWild):
        return "true", None
    if isinstance(pattern, PatternIdent):
        if pattern.name in env:
            return pattern.name, None
        return f'"{_emit_literal(pattern.name)}"', pattern.name
    if isinstance(pattern, PatternLiteral):
        return _emit_expr(pattern.literal, env, func_names), None
    raise ValueError(f"unsupported pattern: {pattern}")


def _emit_expr(
    expr: Expr,
    env: set[str],
    func_names: set[str],
    *,
    in_handler: bool = False,
) -> str:
    if isinstance(expr, NameExpr):
        if expr.name == "self" and "self_" in env:
            return "self_"
        if expr.name in env:
            return expr.name
        if expr.name == "t":
            return "serde_json::json!(true)"
        if expr.name == "f":
            return "serde_json::json!(false)"
        if expr.name == "none":
            return "serde_json::json!(null)"
        return expr.name

    if isinstance(expr, NumberExpr):
        return f"dm::num({expr.value!r})"
    if isinstance(expr, StringExpr):
        return expr.value
    if isinstance(expr, BoolExpr):
        return "serde_json::json!(true)" if expr.value else "serde_json::json!(false)"

    if isinstance(expr, ListExpr):
        items = ", ".join(_emit_expr(x, env, func_names, in_handler=in_handler) for x in expr.items)
        return f"serde_json::json!([{items}])"

    if isinstance(expr, MapExpr):
        items = ", ".join(
            f"{_map_key_text(it.key)}: {_emit_expr(it.value, env, func_names, in_handler=in_handler)}"
            for it in expr.items
        )
        return f"serde_json::json!({{{items}}})"

    if isinstance(expr, UnaryExpr):
        if expr.op == "-":
            return f"dm::binop(\"-\", serde_json::json!(0), {_emit_expr(expr.expr, env, func_names, in_handler=in_handler)})"
        raise ValueError(f"unsupported unary op: {expr.op}")

    if isinstance(expr, BinaryExpr):
        left = _emit_expr(expr.left, env, func_names, in_handler=in_handler)
        right = _emit_expr(expr.right, env, func_names, in_handler=in_handler)
        if expr.op == "/":
            return f"dm::idiv({left}, {right})"
        if expr.op == "$":
            return f"dm::midpoint({left}, {right})"
        if expr.op == "^":
            return f"dm::pow({left}, {right})"
        if expr.op == "&":
            return f"if dm::is_truthy({left}) && dm::is_truthy({right}) {{ serde_json::json!(true) }} else {{ serde_json::json!(false) }}"
        if expr.op == "|":
            return f"if dm::is_truthy({left}) || dm::is_truthy({right}) {{ serde_json::json!(true) }} else {{ serde_json::json!(false) }}"
        if expr.op in {"+", "-", "*", "%", "==", "!=", "<", "<=", ">", ">="}:
            return f"dm::binop({expr.op!r}, {left}, {right})"
        raise ValueError(f"unsupported binary op: {expr.op}")

    if isinstance(expr, TernaryExpr):
        cond = _emit_expr(expr.cond, env, func_names, in_handler=in_handler)
        yes = _emit_expr(expr.then_expr, env, func_names, in_handler=in_handler)
        no = _emit_expr(expr.else_expr, env, func_names, in_handler=in_handler)
        return f"(if dm::is_truthy(&{cond}) {{ {yes} }} else {{ {no} }})"

    if isinstance(expr, SequenceExpr):
        if not expr.items:
            return "serde_json::json!(null)"
        lines = ["{", "    let mut __dm_seq = serde_json::json!(null);"]
        for item in expr.items:
            lines.append(f"    __dm_seq = {_emit_expr(item, env, func_names, in_handler=in_handler)};")
        lines.append("    __dm_seq")
        lines.append("}")
        return "\n".join(lines)

    if isinstance(expr, MatchExpr):
        subject = _emit_expr(expr.subject, env, func_names, in_handler=in_handler)
        lines = ["{", "    let __dm_subject = " + subject + ";"]
        has_fallback = False
        for idx, arm in enumerate(expr.arms):
            cond, capture_name = _emit_pattern(arm.pattern, env, func_names)
            arm_env = set(env)
            if capture_name is not None:
                arm_env.add(capture_name)
            body = _emit_expr(arm.expr, arm_env, func_names, in_handler=in_handler)
            if capture_name is not None:
                has_fallback = True
                if idx == 0:
                    lines.append(f"    if true {{ let {capture_name} = __dm_subject.clone(); {body} }}")
                else:
                    lines.append(f"    else if true {{ let {capture_name} = __dm_subject.clone(); {body} }}")
                continue
            if cond == "true":
                has_fallback = True
                cond_code = "true"
            else:
                cond_code = f"(dm::is_truthy(&__dm_subject) && ( __dm_subject == {cond} ))"
            if idx == 0:
                lines.append(f"    if {cond_code} {{ {body} }}")
            else:
                lines.append(f"    else if {cond_code} {{ {body} }}")
        if expr.arms and not has_fallback:
            lines.append("    else { panic!(\"non-exhaustive match\") }")
        lines.append("}")
        return "\n".join(lines)

    if isinstance(expr, CallExpr):
        if isinstance(expr.func, MemberExpr):
            recv = _emit_expr(expr.func.obj, env, func_names, in_handler=in_handler)
            args = ", ".join(_emit_expr(a, env, func_names, in_handler=in_handler) for a in expr.args)
            return f"__dm_obj_invoke({recv}, {expr.func.name!r}, vec![{args}])"

        args = [_emit_expr(a, env, func_names, in_handler=in_handler) for a in expr.args]
        if isinstance(expr.func, NameExpr):
            name = expr.func.name
            if name in {"fold", "fd"} and len(expr.args) == 5:
                base = args[0]
                init = args[1]
                acc_expr = expr.args[2]
                item_expr = expr.args[3]
                body_expr = expr.args[4]
                if isinstance(acc_expr, NameExpr) and isinstance(item_expr, NameExpr):
                    body = _emit_expr(
                        body_expr,
                        env | {acc_expr.name, item_expr.name},
                        func_names,
                        in_handler=in_handler,
                    )
                    return (
                        "dm::fold("
                        f"{base}, {init}, |"
                        f"{acc_expr.name}: serde_json::Value, {item_expr.name}: serde_json::Value| {body}"
                        ")"
                    )
            if name in _CALL_MAP:
                callee = f"dm::{_CALL_MAP[name]}"
            elif name in func_names:
                callee = name
            else:
                callee = f"dm::{name}"
            arg_list = ", ".join(args)
            return f"{callee}({arg_list})"

        callee = _emit_expr(expr.func, env, func_names, in_handler=in_handler)
        arg_list = ", ".join(args)
        return f"{callee}({arg_list})"

    if isinstance(expr, MemberExpr):
        if isinstance(expr.obj, NameExpr) and expr.obj.name == "self":
            return f"dm::obj_get({_emit_expr(expr.obj, env, func_names, in_handler=in_handler)}, {_map_key_text(expr.name)})"
        return f"dm::member({_emit_expr(expr.obj, env, func_names, in_handler=in_handler)}, {_map_key_text(expr.name)})"

    if isinstance(expr, IndexExpr):
        return f"dm::index({_emit_expr(expr.obj, env, func_names, in_handler=in_handler)}, {_emit_expr(expr.index, env, func_names, in_handler=in_handler)})"

    if isinstance(expr, SliceExpr):
        start = _emit_expr(expr.start, env, func_names, in_handler=in_handler) if expr.start is not None else "serde_json::json!(null)"
        end = _emit_expr(expr.end, env, func_names, in_handler=in_handler) if expr.end is not None else "serde_json::json!(null)"
        return f"dm::slice({_emit_expr(expr.obj, env, func_names, in_handler=in_handler)}, {start}, {end})"

    if isinstance(expr, PatchExpr):
        updates = ", ".join(
            f"{_map_key_text(item.key)}: {_emit_expr(item.value, env, func_names, in_handler=in_handler)}" for item in expr.items
        )
        return f"dm::patch({_emit_expr(expr.obj, env, func_names, in_handler=in_handler)}, serde_json::json!({{{updates}}}))"

    if isinstance(expr, MapBindExpr):
        base = _emit_expr(expr.base, env, func_names, in_handler=in_handler)
        body = _emit_expr(expr.value, env | {expr.key}, func_names, in_handler=in_handler)
        return f"dm::map_bind({base}, |{expr.key}: serde_json::Value| {body})"

    if isinstance(expr, RangeExpr):
        return f"dm::range_inclusive({_emit_expr(expr.start, env, func_names, in_handler=in_handler)}, {_emit_expr(expr.end, env, func_names, in_handler=in_handler)})"

    if isinstance(expr, PropagateExpr):
        return f"dm::propagate(|| {_emit_expr(expr.expr, env, func_names, in_handler=in_handler)})"

    if isinstance(expr, ExceptionMatchExpr):
        err = _emit_expr(expr.exc, env, func_names, in_handler=in_handler)
        types = ", ".join(_emit_expr(t, env, func_names, in_handler=in_handler) for t in expr.types)
        return f"dm::is_exception(&{err}, &[{types}])"

    if isinstance(expr, ReraiseExpr):
        if not in_handler:
            raise ValueError("reraise is only valid inside an error handler")
        return "dm::reraise()"

    if isinstance(expr, TryCatchExpr):
        body = _emit_expr(expr.body, env, func_names, in_handler=False)
        handler = _emit_expr(expr.handler, env | {expr.err_name}, func_names, in_handler=True)
        return f"dm::try_catch(|| {body}, |{expr.err_name}: serde_json::Value| {handler})"

    raise ValueError(f"unsupported expr: {expr}")


def _emit_named_func(decl: FuncDecl, emit_name: str, func_names: set[str], doc_extra: str = "") -> list[str]:
    lines: list[str] = []
    rendered: list[str] = []
    env: set[str] = set()
    arg_names: list[str] = []
    for p in decl.params:
        name = "self_" if p.name == "self" else p.name
        rendered.append(f"{name}: serde_json::Value")
        env.add(name)
        arg_names.append(name)
    sig = ", ".join(rendered)
    args = ", ".join(arg_names)
    tools = ", ".join(f'"{t}"' for t in decl.tools) if decl.tools else ""
    if tools:
        tools = f"&[{tools}]"
    else:
        tools = "&[]"

    lines.append(f"pub fn {emit_name}({sig}) -> serde_json::Value {{")
    if doc_extra:
        lines.append(f"    // {doc_extra}")
    if _has_tool(decl, CapabilityCheckOp):
        lines.append(f"    dm::cap_check({emit_name!r}, {tools});")
    if _has_tool(decl, ResourceIncrementOp):
        lines.append(f"    dm::resource_tick({emit_name!r}, 1);")
    if _has_tool(decl, TraceEntryOp):
        if args:
            lines.append(f'    dm::trace_enter({emit_name!r}, vec![{", ".join(args)}]);')
        else:
            lines.append(f'    dm::trace_enter({emit_name!r}, vec![]);')

    body = _emit_expr(decl.body, env, func_names)
    if _has_tool(decl, ErrorContextOp):
        lines.append("    let __dm_result = match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {")
        lines.append(f"        {body}")
        lines.append("    })) {")
        lines.append("        Ok(__dm_result) => __dm_result,")
        lines.append("        Err(__dm_exc) => {")
        lines.append("            let __dm_err = dm::panic_to_string(__dm_exc);")
        lines.append(f"            panic!(\"{{}}\", dm::with_error_context(&__dm_err, {emit_name!r}));")
        lines.append("        }")
        lines.append("    };")
        if _has_tool(decl, TraceExitOp):
            lines.append(f"    dm::trace_exit({emit_name!r}, &__dm_result);")
        lines.append("    return __dm_result;")
    else:
        lines.append(f"    let __dm_result = {body};")
        if _has_tool(decl, TraceExitOp):
            lines.append(f"    dm::trace_exit({emit_name!r}, &__dm_result);")
        lines.append("    return __dm_result;")

    lines.append("}")
    lines.append("")
    return lines


def _emit_func(decl: FuncDecl, func_names: set[str]) -> list[str]:
    return _emit_named_func(decl, decl.name, func_names)


def _emit_method(decl: MethodDecl, func_names: set[str]) -> list[str]:
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
        func_names,
        doc_extra=f"method:{decl.class_name}.{decl.func_decl.name}",
    )


def _emit_class_ctor(decl: ClassDecl, func_names: set[str]) -> list[str]:
    lines: list[str] = []
    rendered: list[str] = []
    for p in decl.params:
        name = "self_" if p.name == "self" else p.name
        rendered.append(f"{name}: serde_json::Value")
    sig = ", ".join(rendered)

    lines.append(f"pub fn {decl.name}({sig}) -> serde_json::Value {{")
    lines.append("    let mut __dm_fields = serde_json::Map::new();")
    for p in decl.params:
        name = "self_" if p.name == "self" else p.name
        lines.append(f"    __dm_fields.insert({p.name!r}.to_string(), {name});")
    body = _emit_expr(decl.body, {("self_" if p.name == "self" else p.name) for p in decl.params}, func_names)
    lines.append(f"    let __dm_defaults = {body};")
    lines.append("    let mut __dm_obj = dm::obj_new(serde_json::Value::Object(__dm_fields), Some("
                 + repr(decl.name) + "));")
    lines.append("    __dm_obj = dm::patch(__dm_obj, __dm_defaults);")
    lines.append("    return __dm_obj;")
    lines.append("}")
    lines.append("")
    return lines


def _emit_obj_dispatch(methods: list[MethodDecl]) -> list[str]:
    lines: list[str] = []
    lines.append("fn __dm_obj_invoke(obj: serde_json::Value, name: &str, args: Vec<serde_json::Value>) -> serde_json::Value {")
    lines.append("    let class_name = dm::obj_class_name(&obj).unwrap_or_else(|| panic!(\"object has no class binding for method {}\", name));")
    lines.append("    match (class_name, name) {")
    for m in methods:
        sym = _method_name(m.class_name, m.func_decl.name)
        lines.append(f"        ({m.class_name!r}, {m.func_decl.name!r}) => {sym}(obj, "
                     + ", ".join(f"args.get({i}).cloned().unwrap_or(serde_json::Value::Null)" for i, _ in enumerate(m.func_decl.params if m.func_decl.params and m.func_decl.params[0].name == 'self' else m.func_decl.params))
                     + "),")
    lines.append("        _ => panic!(\"unknown method {}__{}\", class_name, name),")
    lines.append("    }")
    lines.append("}")
    lines.append("")
    return lines


def emit(program: Program) -> str:
    lines: list[str] = []
    func_names: set[str] = set()
    methods: list[MethodDecl] = []
    for d in program.decls:
        if isinstance(d, FuncDecl):
            func_names.add(d.name)
        elif isinstance(d, MethodDecl):
            name = _method_name(d.class_name, d.func_decl.name)
            func_names.add(name)
            methods.append(d)
        elif isinstance(d, ClassDecl):
            func_names.add(d.name)
    lines.append("// Auto-generated from Diamond IR (Rust backend, executable mode).")
    lines.append("mod diamond_runtime;")
    lines.append("use std::panic::AssertUnwindSafe;")
    lines.append("")
    lines.append("use diamond_runtime as dm;")
    lines.append(f"// source_module: {program.module_name}")
    lines.append("")
    lines.append("use serde_json::Value;")
    lines.append("")

    for d in program.decls:
        if isinstance(d, FuncDecl):
            lines.extend(_emit_func(d, func_names))
            continue
        if isinstance(d, ClassDecl):
            lines.extend(_emit_class_ctor(d, func_names))
            continue
        if isinstance(d, MethodDecl):
            lines.extend(_emit_method(d, func_names))
            continue
        raise ValueError(f"unsupported top-level declaration: {type(d).__name__}")

    lines.extend(_emit_obj_dispatch(methods))

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"
