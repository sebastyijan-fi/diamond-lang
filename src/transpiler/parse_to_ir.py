"""Parse Diamond source into language-agnostic IR."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
import re
from typing import NamedTuple

from lark import Lark, Token, Tree

from diamond_ir import (
    BinaryExpr,
    BoolExpr,
    CapabilityCheckOp,
    CallExpr,
    ClassDecl,
    ErrorContextOp,
    ExceptionMatchExpr,
    Expr,
    FuncDecl,
    IndexExpr,
    ListExpr,
    MapBindExpr,
    MapExpr,
    MapItem,
    MatchArm,
    MatchExpr,
    MethodDecl,
    MemberExpr,
    NameExpr,
    NumberExpr,
    Param,
    PatchExpr,
    Pattern,
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
    TypeField,
    TypeList,
    TypeName,
    TypeRecord,
    UnaryExpr,
)
from grammar import DIAMOND_GRAMMAR


def build_parser() -> Lark:
    return Lark(DIAMOND_GRAMMAR, parser="lalr", start="start", propagate_positions=True)


def build_top_level_decl_parser() -> Lark:
    return Lark(DIAMOND_GRAMMAR, parser="lalr", start="top_level_decl", propagate_positions=True)


def _expect_tree(node: Tree | Token, data: str) -> Tree:
    if not isinstance(node, Tree) or node.data != data:
        raise ValueError(f"expected tree {data}, got {node}")
    return node


def _parse_type(node: Tree | Token) -> TypeExpr:
    if isinstance(node, Token):
        return TypeName(name=str(node))

    t = _expect_tree(node, "type")
    if not t.children:
        raise ValueError("empty type")

    children = [ch for ch in t.children if ch is not None]
    if any(isinstance(ch, Tree) and ch.data == "type_field" for ch in children):
        fields: list[TypeField] = []
        for ch in children:
            field = _expect_tree(ch, "type_field")
            if len(field.children) != 2 or not isinstance(field.children[0], Token):
                raise ValueError("invalid type_field")
            fields.append(TypeField(name=str(field.children[0]), type_expr=_parse_type(field.children[1])))
        return TypeRecord(fields=fields)

    if len(children) == 1 and isinstance(children[0], Token):
        return TypeName(name=str(children[0]))

    if len(children) == 1 and isinstance(children[0], Tree) and children[0].data == "type":
        return TypeList(inner=_parse_type(children[0]))

    raise ValueError(f"unsupported type form: {t}")


def _parse_pattern(node: Tree | Token) -> Pattern:
    p = _expect_tree(node, "pattern")
    if not p.children:
        return PatternWild()
    child = p.children[0]
    if isinstance(child, Token) and child.type == "IDENT":
        return PatternIdent(name=str(child))
    return PatternLiteral(literal=_parse_expr(child))


def _parse_map_item(node: Tree | Token) -> MapItem:
    item = _expect_tree(node, "map_item")
    if len(item.children) != 2:
        raise ValueError("invalid map_item")
    key_node, val_node = item.children
    if not isinstance(key_node, Token):
        raise ValueError("invalid map key")
    key = str(key_node)
    key_is_string = key_node.type == "STRING"
    return MapItem(key=key, key_is_string=key_is_string, value=_parse_expr(val_node))


class _ModuleBlock(NamedTuple):
    name: str
    caps: tuple[str, ...]
    body: str


class _ContractDecl(NamedTuple):
    name: str
    params: tuple[str, ...]


def _skip_ws(source: str, i: int) -> int:
    n = len(source)
    while i < n:
        while i < n and source[i].isspace():
            i += 1
        if i + 1 < n and source[i] == "/" and source[i + 1] == "/":
            i += 2
            while i < n and source[i] not in "\r\n":
                i += 1
            continue
        break
    return i


_CONTRACT_LINE_RE = re.compile(r"^\s*//\s*@([A-Za-z_][A-Za-z0-9_]*)\s+exposes\s+(.+?)\s*$")
_CONTRACT_DECL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*>\s*(.+)$")


def _split_top_level(text: str, sep: str = ",") -> list[str]:
    out: list[str] = []
    start = 0
    depth_paren = 0
    depth_brack = 0
    depth_brace = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "(":
            depth_paren += 1
            continue
        if ch == ")":
            depth_paren = max(depth_paren - 1, 0)
            continue
        if ch == "[":
            depth_brack += 1
            continue
        if ch == "]":
            depth_brack = max(depth_brack - 1, 0)
            continue
        if ch == "{":
            depth_brace += 1
            continue
        if ch == "}":
            depth_brace = max(depth_brace - 1, 0)
            continue
        if ch == sep and depth_paren == 0 and depth_brack == 0 and depth_brace == 0:
            part = text[start:i].strip()
            if part:
                out.append(part)
            start = i + 1
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return out


def _parse_contract_decl(text: str, module_name: str, line_no: int, block_name: str) -> _ContractDecl:
    m = _CONTRACT_DECL_RE.match(text.strip())
    if not m:
        raise ValueError(f"{module_name}: malformed contract decl at line {line_no}: {text!r}")
    fn_name = m.group(1)
    params_raw = m.group(2).strip()
    if fn_name.startswith("_"):
        raise ValueError(f"{module_name}: contract cannot expose private symbol {block_name}.{fn_name}")
    params: list[str] = []
    if params_raw:
        for part in _split_top_level(params_raw):
            if ":" in part:
                lhs = part.split(":", 1)[0].strip()
                if lhs:
                    params.append(lhs)
                    continue
            raise ValueError(
                f"{module_name}: malformed contract param in {block_name}.{fn_name} at line {line_no}: {part!r}"
            )
    return _ContractDecl(name=fn_name, params=tuple(params))


def _extract_contract_exports(
    source: str, module_name: str
) -> tuple[list[str], dict[str, dict[str, _ContractDecl]]]:
    order: list[str] = []
    out: dict[str, dict[str, _ContractDecl]] = {}
    for ln, raw_line in enumerate(source.splitlines(), start=1):
        m = _CONTRACT_LINE_RE.match(raw_line)
        if not m:
            continue
        block_name = m.group(1)
        payload = m.group(2).strip()
        if block_name not in out:
            out[block_name] = {}
            order.append(block_name)
        for part in _split_top_level(payload):
            d = _parse_contract_decl(part, module_name, ln, block_name)
            prev = out[block_name].get(d.name)
            if prev is not None and prev.params != d.params:
                raise ValueError(
                    f"{module_name}: conflicting contract signatures for {block_name}.{d.name}"
                )
            out[block_name][d.name] = d
    return order, out


def _scan_ident(source: str, i: int) -> tuple[str, int]:
    n = len(source)
    if i >= n or not (source[i].isalpha() or source[i] == "_"):
        raise ValueError(f"expected identifier at offset {i}")
    j = i + 1
    while j < n and (source[j].isalnum() or source[j] == "_"):
        j += 1
    return source[i:j], j


def _scan_bracket_content(source: str, i: int, module_name: str) -> tuple[str, int]:
    n = len(source)
    if i >= n or source[i] != "[":
        raise ValueError(f"{module_name}: expected '[' at offset {i}")
    j = i + 1
    while j < n and source[j] != "]":
        j += 1
    if j >= n:
        raise ValueError(f"{module_name}: unterminated capability bracket")
    return source[i + 1 : j], j + 1


def _scan_braced_body(source: str, i: int, module_name: str) -> tuple[str, int]:
    n = len(source)
    if i >= n or source[i] != "{":
        raise ValueError(f"{module_name}: expected '{{' at offset {i}")
    depth = 1
    j = i + 1
    in_string = False
    escape = False
    while j < n:
        ch = source[j]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            j += 1
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[i + 1 : j], j + 1
        j += 1
    raise ValueError(f"{module_name}: unterminated block body")


def _parse_caps(raw: str, module_name: str, block_name: str) -> tuple[str, ...]:
    payload = raw.strip()
    if not payload:
        return ()
    if not payload.startswith("cap:"):
        raise ValueError(f"{module_name}: @{block_name} only supports [cap:...] metadata")
    items = [part.strip() for part in payload[4:].split(",")]
    caps = tuple(part for part in items if part)
    return caps


def _extract_module_blocks(source: str, module_name: str) -> list[_ModuleBlock] | None:
    i = _skip_ws(source, 0)
    if i >= len(source) or source[i] != "@":
        return None

    blocks: list[_ModuleBlock] = []
    n = len(source)
    while True:
        i = _skip_ws(source, i)
        if i >= n:
            break
        if source[i] != "@":
            raise ValueError(f"{module_name}: expected '@' block start at offset {i}")
        i += 1
        block_name, i = _scan_ident(source, i)
        i = _skip_ws(source, i)
        caps: tuple[str, ...] = ()
        if i < n and source[i] == "[":
            cap_raw, i = _scan_bracket_content(source, i, module_name)
            caps = _parse_caps(cap_raw, module_name, block_name)
            i = _skip_ws(source, i)
        body, i = _scan_braced_body(source, i, module_name)
        blocks.append(_ModuleBlock(name=block_name, caps=caps, body=body))
        i = _skip_ws(source, i)
        if i < n and source[i] == ";":
            i += 1
        i = _skip_ws(source, i)
        if i >= n:
            break
    return blocks


def _mangle(block_name: str, fn_name: str) -> str:
    return f"{block_name}__{fn_name}"


def _collect_module_block_dependencies(
    expr: Expr,
    *,
    current_block: str,
    scope: set[str],
    block_decls: dict[str, dict[str, FuncDecl]],
) -> set[str]:
    deps: set[str] = set()

    def _walk(node: object, local_scope: set[str]) -> None:
        if isinstance(node, MemberExpr) and isinstance(node.obj, NameExpr):
            owner = node.obj.name
            if owner not in local_scope and owner in block_decls and owner != current_block:
                deps.add(owner)

        if isinstance(node, MapBindExpr):
            _walk(node.base, local_scope)
            _walk(node.value, local_scope | {node.key})
            return

        if isinstance(node, TryCatchExpr):
            _walk(node.body, local_scope)
            _walk(node.handler, local_scope | {node.err_name})
            return

        if isinstance(node, MatchExpr):
            _walk(node.subject, local_scope)
            for arm in node.arms:
                arm_scope = local_scope
                if isinstance(arm.pattern, PatternIdent):
                    arm_scope = local_scope | {arm.pattern.name}
                elif isinstance(arm.pattern, PatternLiteral):
                    _walk(arm.pattern.literal, local_scope)
                _walk(arm.expr, arm_scope)
            return

        if isinstance(node, list | tuple):
            for item in node:
                _walk(item, local_scope)
            return

        if is_dataclass(node):
            for f in fields(node):
                _walk(getattr(node, f.name), local_scope)
            return

    _walk(expr, scope)
    return deps


def _find_module_block_cycle(
    block_deps: dict[str, set[str]],
    block_order: list[str],
) -> list[str] | None:
    state = {name: 0 for name in block_order}
    stack: list[str] = []
    stack_pos: dict[str, int] = {}
    index = {name: i for i, name in enumerate(block_order)}

    def _visit(name: str) -> list[str] | None:
        state[name] = 1
        stack_pos[name] = len(stack)
        stack.append(name)
        for dep in sorted(block_deps.get(name, set()), key=lambda n: index[n]):
            dep_state = state.get(dep, 0)
            if dep_state == 0:
                cycle = _visit(dep)
                if cycle is not None:
                    return cycle
                continue
            if dep_state == 1:
                start = stack_pos[dep]
                return stack[start:] + [dep]
        stack.pop()
        stack_pos.pop(name, None)
        state[name] = 2
        return None

    for name in block_order:
        if state[name] != 0:
            continue
        cycle = _visit(name)
        if cycle is not None:
            return cycle
    return None


def _deterministic_module_block_order(
    block_order: list[str],
    block_deps: dict[str, set[str]],
    *,
    module_name: str,
) -> list[str]:
    if not block_order:
        return []

    block_set = set(block_order)
    filtered_deps: dict[str, set[str]] = {
        name: {dep for dep in block_deps.get(name, set()) if dep in block_set and dep != name}
        for name in block_order
    }

    cycle = _find_module_block_cycle(filtered_deps, block_order)
    if cycle is not None:
        rendered = " -> ".join(f"@{name}" for name in cycle)
        raise ValueError(f"{module_name}: module block cycle detected: {rendered}")

    dependents: dict[str, set[str]] = {name: set() for name in block_order}
    indegree: dict[str, int] = {name: 0 for name in block_order}
    for name in block_order:
        deps = filtered_deps[name]
        indegree[name] = len(deps)
        for dep in deps:
            dependents[dep].add(name)

    index = {name: i for i, name in enumerate(block_order)}
    ready = sorted((name for name, deg in indegree.items() if deg == 0), key=lambda n: index[n])
    ordered: list[str] = []
    while ready:
        cur = ready.pop(0)
        ordered.append(cur)
        for nxt in sorted(dependents[cur], key=lambda n: index[n]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
        ready.sort(key=lambda n: index[n])

    if len(ordered) != len(block_order):
        raise ValueError(f"{module_name}: failed to resolve deterministic module block order")

    return ordered


def _rewrite_expr_for_modules(
    expr: Expr,
    *,
    module_name: str,
    current_block: str,
    scope: set[str],
    block_decls: dict[str, dict[str, FuncDecl]],
) -> Expr:
    local_names = set(block_decls[current_block].keys())

    if isinstance(expr, NameExpr):
        if expr.name in scope:
            return expr
        if expr.name in local_names:
            return NameExpr(name=_mangle(current_block, expr.name))
        return expr

    if isinstance(expr, NumberExpr | StringExpr | BoolExpr | ReraiseExpr):
        return expr

    if isinstance(expr, UnaryExpr):
        return UnaryExpr(
            op=expr.op,
            expr=_rewrite_expr_for_modules(
                expr.expr,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
        )

    if isinstance(expr, BinaryExpr):
        return BinaryExpr(
            op=expr.op,
            left=_rewrite_expr_for_modules(
                expr.left,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            right=_rewrite_expr_for_modules(
                expr.right,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
        )

    if isinstance(expr, TernaryExpr):
        return TernaryExpr(
            cond=_rewrite_expr_for_modules(
                expr.cond,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            then_expr=_rewrite_expr_for_modules(
                expr.then_expr,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            else_expr=_rewrite_expr_for_modules(
                expr.else_expr,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
        )

    if isinstance(expr, SequenceExpr):
        return SequenceExpr(
            items=[
                _rewrite_expr_for_modules(
                    item,
                    module_name=module_name,
                    current_block=current_block,
                    scope=scope,
                    block_decls=block_decls,
                )
                for item in expr.items
            ]
        )

    if isinstance(expr, MatchExpr):
        arms: list[MatchArm] = []
        for arm in expr.arms:
            pat = arm.pattern
            if isinstance(pat, PatternLiteral):
                pat = PatternLiteral(
                    literal=_rewrite_expr_for_modules(
                        pat.literal,
                        module_name=module_name,
                        current_block=current_block,
                        scope=scope,
                        block_decls=block_decls,
                    )
                )
            arms.append(
                MatchArm(
                    pattern=pat,
                    expr=_rewrite_expr_for_modules(
                        arm.expr,
                        module_name=module_name,
                        current_block=current_block,
                        scope=scope,
                        block_decls=block_decls,
                    ),
                )
            )
        return MatchExpr(
            subject=_rewrite_expr_for_modules(
                expr.subject,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            arms=arms,
        )

    if isinstance(expr, CallExpr):
        return CallExpr(
            func=_rewrite_expr_for_modules(
                expr.func,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            args=[
                _rewrite_expr_for_modules(
                    arg,
                    module_name=module_name,
                    current_block=current_block,
                    scope=scope,
                    block_decls=block_decls,
                )
                for arg in expr.args
            ],
        )

    if isinstance(expr, MemberExpr):
        if isinstance(expr.obj, NameExpr):
            owner = expr.obj.name
            if owner not in scope:
                if owner not in block_decls:
                    raise ValueError(
                        f"{module_name}: unknown block qualifier '{owner}' in {owner}.{expr.name}"
                    )
                target = block_decls[owner]
                if expr.name not in target:
                    raise ValueError(
                        f"{module_name}: missing symbol {owner}.{expr.name}"
                    )
                if expr.name.startswith("_") and owner != current_block:
                    raise ValueError(
                        f"{module_name}: private symbol access denied for {owner}.{expr.name}"
                    )
                return NameExpr(name=_mangle(owner, expr.name))
        return MemberExpr(
            obj=_rewrite_expr_for_modules(
                expr.obj,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            name=expr.name,
        )

    if isinstance(expr, IndexExpr):
        return IndexExpr(
            obj=_rewrite_expr_for_modules(
                expr.obj,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            index=_rewrite_expr_for_modules(
                expr.index,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
        )

    if isinstance(expr, SliceExpr):
        return SliceExpr(
            obj=_rewrite_expr_for_modules(
                expr.obj,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            start=(
                _rewrite_expr_for_modules(
                    expr.start,
                    module_name=module_name,
                    current_block=current_block,
                    scope=scope,
                    block_decls=block_decls,
                )
                if expr.start is not None
                else None
            ),
            end=(
                _rewrite_expr_for_modules(
                    expr.end,
                    module_name=module_name,
                    current_block=current_block,
                    scope=scope,
                    block_decls=block_decls,
                )
                if expr.end is not None
                else None
            ),
        )

    if isinstance(expr, PatchExpr):
        return PatchExpr(
            obj=_rewrite_expr_for_modules(
                expr.obj,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            items=[
                MapItem(
                    key=item.key,
                    key_is_string=item.key_is_string,
                    value=_rewrite_expr_for_modules(
                        item.value,
                        module_name=module_name,
                        current_block=current_block,
                        scope=scope,
                        block_decls=block_decls,
                    ),
                )
                for item in expr.items
            ],
        )

    if isinstance(expr, MapBindExpr):
        return MapBindExpr(
            base=_rewrite_expr_for_modules(
                expr.base,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            key=expr.key,
            value=_rewrite_expr_for_modules(
                expr.value,
                module_name=module_name,
                current_block=current_block,
                scope=scope | {expr.key},
                block_decls=block_decls,
            ),
        )

    if isinstance(expr, RangeExpr):
        return RangeExpr(
            start=_rewrite_expr_for_modules(
                expr.start,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            end=_rewrite_expr_for_modules(
                expr.end,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
        )

    if isinstance(expr, PropagateExpr):
        return PropagateExpr(
            expr=_rewrite_expr_for_modules(
                expr.expr,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            )
        )

    if isinstance(expr, ExceptionMatchExpr):
        return ExceptionMatchExpr(
            exc=_rewrite_expr_for_modules(
                expr.exc,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            types=[
                _rewrite_expr_for_modules(
                    t,
                    module_name=module_name,
                    current_block=current_block,
                    scope=scope,
                    block_decls=block_decls,
                )
                for t in expr.types
            ],
        )

    if isinstance(expr, TryCatchExpr):
        return TryCatchExpr(
            body=_rewrite_expr_for_modules(
                expr.body,
                module_name=module_name,
                current_block=current_block,
                scope=scope,
                block_decls=block_decls,
            ),
            err_name=expr.err_name,
            handler=_rewrite_expr_for_modules(
                expr.handler,
                module_name=module_name,
                current_block=current_block,
                scope=scope | {expr.err_name},
                block_decls=block_decls,
            ),
        )

    if isinstance(expr, ListExpr):
        return ListExpr(
            items=[
                _rewrite_expr_for_modules(
                    item,
                    module_name=module_name,
                    current_block=current_block,
                    scope=scope,
                    block_decls=block_decls,
                )
                for item in expr.items
            ]
        )

    if isinstance(expr, MapExpr):
        return MapExpr(
            items=[
                MapItem(
                    key=item.key,
                    key_is_string=item.key_is_string,
                    value=_rewrite_expr_for_modules(
                        item.value,
                        module_name=module_name,
                        current_block=current_block,
                        scope=scope,
                        block_decls=block_decls,
                    ),
                )
                for item in expr.items
            ]
        )

    raise ValueError(f"unsupported module rewrite node: {type(expr).__name__}")


def _extern_stub_decl(block_name: str, decl: _ContractDecl) -> FuncDecl:
    params = [Param(name=p, type_expr=TypeName(name="O")) for p in decl.params]
    args_list = ListExpr(items=[NameExpr(name=p) for p in decl.params])
    body = CallExpr(
        func=NameExpr(name="ext"),
        args=[StringExpr(value=f"\"{block_name}.{decl.name}\""), args_list],
    )
    return FuncDecl(
        name=_mangle(block_name, decl.name),
        params=params,
        return_type=TypeName(name="O"),
        body=body,
        tools=[],
        tool_ops=[],
    )


def _resolve_module_blocks(
    blocks: list[_ModuleBlock],
    module_name: str,
    parser: Lark,
    contract_order: list[str] | None = None,
    contract_exports: dict[str, dict[str, _ContractDecl]] | None = None,
) -> Program:
    contract_order = contract_order or []
    contract_exports = contract_exports or {}

    block_decls: dict[str, dict[str, FuncDecl]] = {}
    block_caps: dict[str, tuple[str, ...]] = {}
    block_order: list[str] = []
    for block in blocks:
        if block.name in block_decls:
            raise ValueError(f"{module_name}: duplicate block @{block.name}")
        parsed = parse_source(block.body, module_name=f"{module_name}@{block.name}", parser=parser)
        decl_map: dict[str, FuncDecl] = {}
        for decl in parsed.decls:
            if not isinstance(decl, FuncDecl):
                raise ValueError(
                    f"{module_name}: module block @{block.name} only supports function declarations"
                )
            if decl.name in decl_map:
                raise ValueError(
                    f"{module_name}: duplicate declaration {block.name}.{decl.name}"
                )
            decl_map[decl.name] = decl
        block_decls[block.name] = decl_map
        block_caps[block.name] = block.caps
        block_order.append(block.name)

    for c_block, c_decl_map in contract_exports.items():
        if c_block in block_decls:
            local = block_decls[c_block]
            for sym in c_decl_map:
                if sym not in local:
                    raise ValueError(
                        f"{module_name}: contract mismatch for @{c_block}; missing local symbol {c_block}.{sym}"
                    )
            continue
        block_decls[c_block] = {
            sym: FuncDecl(
                name=sym,
                params=[Param(name=p, type_expr=TypeName(name="O")) for p in c_decl.params],
                return_type=TypeName(name="O"),
                body=NameExpr(name="none"),
                tools=[],
                tool_ops=[],
            )
            for sym, c_decl in c_decl_map.items()
        }

    rewritten_blocks: dict[str, list[FuncDecl]] = {}
    block_deps: dict[str, set[str]] = {name: set() for name in block_order}
    for block_name in block_order:
        rewritten_decls: list[FuncDecl] = []
        for decl in block_decls[block_name].values():
            scope = {p.name for p in decl.params}
            block_deps[block_name].update(
                _collect_module_block_dependencies(
                    decl.body,
                    current_block=block_name,
                    scope=scope,
                    block_decls=block_decls,
                )
            )
            rewritten = _rewrite_expr_for_modules(
                decl.body,
                module_name=module_name,
                current_block=block_name,
                scope=scope,
                block_decls=block_decls,
            )
            merged_tools = list(decl.tools)
            if block_caps[block_name]:
                if "c" not in merged_tools:
                    merged_tools.append("c")
                for cap in block_caps[block_name]:
                    if cap not in merged_tools:
                        merged_tools.append(cap)
            rewritten_decls.append(
                FuncDecl(
                    name=_mangle(block_name, decl.name),
                    params=decl.params,
                    return_type=decl.return_type,
                    body=rewritten,
                    tools=merged_tools,
                    tool_ops=_tool_ops_from_symbols(merged_tools),
                )
            )
        rewritten_blocks[block_name] = rewritten_decls

    ordered_blocks = _deterministic_module_block_order(
        block_order,
        block_deps,
        module_name=module_name,
    )

    out_decls: list[FuncDecl] = []
    for block_name in ordered_blocks:
        out_decls.extend(rewritten_blocks[block_name])

    for c_block in contract_order:
        if c_block in block_caps:
            # Real block exists; no external stubs needed.
            continue
        for c_decl in contract_exports.get(c_block, {}).values():
            out_decls.append(_extern_stub_decl(c_block, c_decl))

    return Program(module_name=module_name, decls=out_decls)


def _parse_left_assoc(children: list[Tree | Token]) -> Expr:
    if not children:
        raise ValueError("missing expression")
    out = _parse_expr(children[0])
    i = 1
    while i < len(children):
        if i + 1 >= len(children) or not isinstance(children[i], Token):
            raise ValueError(f"invalid infix sequence: {children}")
        out = BinaryExpr(op=str(children[i]), left=out, right=_parse_expr(children[i + 1]))
        i += 2
    return out


def _parse_postfix(node: Tree) -> Expr:
    if not node.children:
        raise ValueError("empty postfix")
    children = [ch for ch in node.children if ch is not None]
    out = _parse_expr(children[0])

    def _apply_index_like(base: Expr, inner: Tree | Token) -> Expr:
        if isinstance(inner, Tree) and inner.data == "slice_or_index":
            if len(inner.children) == 1:
                return IndexExpr(obj=base, index=_parse_expr(inner.children[0]))
            if len(inner.children) == 2:
                start = _parse_expr(inner.children[0]) if inner.children[0] is not None else None
                end = _parse_expr(inner.children[1]) if inner.children[1] is not None else None
                return SliceExpr(obj=base, start=start, end=end)
            raise ValueError("invalid slice_or_index")
        return IndexExpr(obj=base, index=_parse_expr(inner))

    for op in children[1:]:
        if not isinstance(op, Tree):
            raise ValueError("invalid postfix operator")
        op_tree = op

        if op_tree.data == "call":
            args = [_parse_expr(ch) for ch in op_tree.children if ch is not None]
            out = CallExpr(func=out, args=args)
            continue

        if op_tree.data == "member":
            if len(op_tree.children) != 1 or not isinstance(op_tree.children[0], Token):
                raise ValueError("invalid member access")
            out = MemberExpr(obj=out, name=str(op_tree.children[0]))
            continue

        if op_tree.data == "propagate_index":
            op_children = [
                ch
                for ch in op_tree.children
                if not (isinstance(ch, Token) and ch.type == "PROP_INDEX_QMARK")
            ]
            if len(op_children) != 1:
                raise ValueError("invalid propagate_index")
            out = _apply_index_like(PropagateExpr(expr=out), op_children[0])
            continue

        if op_tree.data == "index":
            if len(op_tree.children) != 1:
                raise ValueError("invalid index/slice")
            out = _apply_index_like(out, op_tree.children[0])
            continue

        if op_tree.data == "patch":
            items = [_parse_map_item(ch) for ch in op_tree.children if ch is not None]
            out = PatchExpr(obj=out, items=items)
            continue

        if op_tree.data == "propagate":
            out = PropagateExpr(expr=out)
            continue

        raise ValueError(f"unsupported postfix op: {op_tree.data}")

    return out


def _parse_expr(node: Tree | Token) -> Expr:
    if isinstance(node, Token):
        if node.type == "IDENT":
            return NameExpr(name=str(node))
        if node.type == "NUMBER":
            return NumberExpr(value=str(node))
        if node.type == "STRING":
            return StringExpr(value=str(node))
        if node.type == "TRUE":
            return BoolExpr(value=True)
        if node.type == "FALSE":
            return BoolExpr(value=False)
        raise ValueError(f"unexpected token in expr: {node.type}")

    if node.data in {"expr", "primary", "literal"}:
        if not node.children:
            raise ValueError(f"empty node: {node.data}")
        return _parse_expr(node.children[0])

    if node.data == "self_ref":
        return NameExpr(name="self")

    if node.data == "try_catch":
        children = [ch for ch in node.children if not (isinstance(ch, Token) and ch.type == "TRY")]
        if len(children) != 3 or not isinstance(children[1], Token):
            raise ValueError("invalid try_catch")
        return TryCatchExpr(
            body=_parse_expr(children[0]),
            err_name=str(children[1]),
            handler=_parse_expr(children[2]),
        )

    if node.data == "seq":
        children = [ch for ch in node.children if not (isinstance(ch, Token) and ch.type == "SEMI")]
        if len(children) == 1:
            return _parse_expr(children[0])
        return SequenceExpr(items=[_parse_expr(ch) for ch in children])

    if node.data in {"cond", "cond_no_match"}:
        children = [ch for ch in node.children if not (isinstance(ch, Token) and ch.type == "QMARK")]
        if len(children) == 1:
            return _parse_expr(children[0])
        if len(children) == 3:
            return TernaryExpr(
                cond=_parse_expr(children[0]),
                then_expr=_parse_expr(children[1]),
                else_expr=_parse_expr(children[2]),
            )
        raise ValueError(f"invalid {node.data}")

    if node.data == "match":
        if not node.children:
            raise ValueError("invalid match")
        subject = _parse_expr(node.children[0])
        if len(node.children) == 1:
            return subject
        arms: list[MatchArm] = []
        for child in node.children[1:]:
            arm = _expect_tree(child, "match_arm")
            if len(arm.children) != 2:
                raise ValueError("invalid match_arm")
            arms.append(MatchArm(pattern=_parse_pattern(arm.children[0]), expr=_parse_expr(arm.children[1])))
        return MatchExpr(subject=subject, arms=arms)

    if node.data in {"or_expr", "and_expr", "cmp_expr", "add_expr", "mul_expr", "pow_expr"}:
        return _parse_left_assoc(node.children)

    if node.data == "map_expr":
        if len(node.children) == 1:
            return _parse_expr(node.children[0])
        if len(node.children) == 4 and isinstance(node.children[1], Token):
            base = _parse_expr(node.children[0])
            key = node.children[2]
            if not isinstance(key, Token):
                raise ValueError("invalid map bind key")
            return MapBindExpr(base=base, key=str(key), value=_parse_expr(node.children[3]))
        raise ValueError("invalid map_expr")

    if node.data == "range_expr":
        if len(node.children) == 1:
            return _parse_expr(node.children[0])
        if len(node.children) == 3:
            return RangeExpr(start=_parse_expr(node.children[0]), end=_parse_expr(node.children[2]))
        raise ValueError("invalid range_expr")

    if node.data == "neg":
        if len(node.children) != 1:
            raise ValueError("invalid neg")
        return UnaryExpr(op="-", expr=_parse_expr(node.children[0]))

    if node.data == "reraise":
        return ReraiseExpr()

    if node.data == "exc_match":
        children = [ch for ch in node.children if not (isinstance(ch, Token) and ch.type == "ISEXC")]
        if len(children) < 2:
            raise ValueError("invalid exc_match")
        return ExceptionMatchExpr(exc=_parse_expr(children[0]), types=[_parse_expr(ch) for ch in children[1:]])

    if node.data == "postfix":
        return _parse_postfix(node)

    if node.data == "list_lit":
        return ListExpr(items=[_parse_expr(ch) for ch in node.children if ch is not None])

    if node.data == "map_lit":
        return MapExpr(items=[_parse_map_item(ch) for ch in node.children if ch is not None])

    if node.data == "slice_or_index":
        if len(node.children) == 1:
            return _parse_expr(node.children[0])
        raise ValueError("slice_or_index should be handled by index op")

    raise ValueError(f"unsupported expr node: {node.data}")


def _parse_decl(node: Tree) -> FuncDecl:
    children = [ch for ch in node.children if ch is not None]
    if not children or not isinstance(children[0], Token):
        raise ValueError("invalid declaration")

    name = str(children[0])
    i = 1

    tools: list[str] = []
    if i < len(children) and isinstance(children[i], Tree) and children[i].data == "tool_header":
        tools = [str(ch) for ch in children[i].children if isinstance(ch, Token)]
        i += 1

    params: list[Param] = []
    while i < len(children) and isinstance(children[i], Tree) and children[i].data == "param":
        p = children[i]
        if len(p.children) != 2 or not isinstance(p.children[0], Token):
            raise ValueError(f"invalid param in {name}")
        params.append(Param(name=str(p.children[0]), type_expr=_parse_type(p.children[1])))
        i += 1

    if i >= len(children) - 1:
        raise ValueError(f"missing return type or body in {name}")

    ret = _parse_type(children[i])
    body_node = children[i + 1]
    if not isinstance(body_node, Tree) and not isinstance(body_node, Token):
        raise ValueError(f"invalid body expr in {name}")

    body = _parse_expr(body_node)
    tool_ops = _tool_ops_from_symbols(tools)
    return FuncDecl(name=name, params=params, return_type=ret, body=body, tools=tools, tool_ops=tool_ops)


def _parse_class_decl(node: Tree) -> ClassDecl:
    children = [
        ch
        for ch in node.children
        if ch is not None and not (isinstance(ch, Token) and ch.type == "CLASS_SIGIL")
    ]
    if not children or not isinstance(children[0], Token):
        raise ValueError("invalid class declaration")

    name = str(children[0])
    i = 1
    params: list[Param] = []
    while i < len(children) and isinstance(children[i], Tree) and children[i].data == "param":
        p = children[i]
        if len(p.children) != 2 or not isinstance(p.children[0], Token):
            raise ValueError(f"invalid param in class {name}")
        params.append(Param(name=str(p.children[0]), type_expr=_parse_type(p.children[1])))
        i += 1

    if i >= len(children):
        raise ValueError(f"class {name} missing body")
    body_node = children[i]
    if not isinstance(body_node, (Tree, Token)):
        raise ValueError(f"invalid class body in {name}")
    body = _parse_expr(body_node)
    return ClassDecl(name=name, params=params, body=body)


def _parse_method_decl(node: Tree) -> MethodDecl:
    children = [ch for ch in node.children if ch is not None]
    if len(children) < 4:
        raise ValueError("invalid method declaration")
    if not isinstance(children[0], Token) or not isinstance(children[1], Token):
        raise ValueError("invalid method class/name")

    class_name = str(children[0])
    name = str(children[1])
    i = 2

    tools: list[str] = []
    if i < len(children) and isinstance(children[i], Tree) and children[i].data == "tool_header":
        tools = [str(ch) for ch in children[i].children if isinstance(ch, Token)]
        i += 1

    params: list[Param] = []
    while i < len(children) and isinstance(children[i], Tree) and children[i].data == "param":
        p = children[i]
        if len(p.children) != 2 or not isinstance(p.children[0], Token):
            raise ValueError(f"invalid param in method {class_name}.{name}")
        params.append(Param(name=str(p.children[0]), type_expr=_parse_type(p.children[1])))
        i += 1

    if i >= len(children) - 1:
        raise ValueError(f"missing return type or body in method {class_name}.{name}")

    ret = _parse_type(children[i])
    body_node = children[i + 1]
    if not isinstance(body_node, (Tree, Token)):
        raise ValueError(f"invalid body in method {class_name}.{name}")
    body = _parse_expr(body_node)
    tool_ops = _tool_ops_from_symbols(tools)
    return MethodDecl(
        class_name=class_name,
        func_decl=FuncDecl(
            name=name,
            params=params,
            return_type=ret,
            body=body,
            tools=tools,
            tool_ops=tool_ops,
        ),
    )


def _parse_top_level_decl(node: Tree) -> FuncDecl | ClassDecl | MethodDecl:
    if node.data == "top_level_decl":
        children = [ch for ch in node.children if isinstance(ch, Tree)]
        if len(children) != 1:
            raise ValueError("invalid top_level_decl")
        return _parse_top_level_decl(children[0])
    if node.data == "func_decl":
        return _parse_decl(node)
    if node.data == "class_decl":
        return _parse_class_decl(node)
    if node.data == "method_decl":
        return _parse_method_decl(node)
    if node.data == "decorator_decl":
        raise ValueError("decorator declarations are not supported by parse_to_ir yet")
    raise ValueError(f"unsupported top-level declaration: {node.data}")


def _tool_ops_from_symbols(tools: list[str]) -> list[ToolOp]:
    ops: list[ToolOp] = []
    for t in tools:
        if t == "t":
            ops.append(TraceEntryOp())
            ops.append(TraceExitOp())
        elif t == "c":
            ops.append(CapabilityCheckOp(required=[]))
        elif t == "b":
            ops.append(ResourceIncrementOp(counter="steps"))
        elif t == "e":
            ops.append(ErrorContextOp())
    return ops


def _is_comment_only_chunk(text: str) -> bool:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line and not line.startswith("//"):
            return False
    return True


def _split_top_level_decls(source: str) -> list[str]:
    chunks: list[str] = []
    buf: list[str] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    in_string = False
    escaped = False
    i = 0
    n = len(source)

    def flush() -> None:
        nonlocal buf
        text = "".join(buf).strip()
        if text and not _is_comment_only_chunk(text):
            chunks.append(text)
        buf = []

    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        if in_string:
            buf.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            buf.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            while i < n and source[i] not in "\n\r":
                buf.append(source[i])
                i += 1
            continue

        if ch == "(":
            paren_depth += 1
        elif ch == ")" and paren_depth > 0:
            paren_depth -= 1
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]" and bracket_depth > 0:
            bracket_depth -= 1
        elif ch == "{":
            brace_depth += 1
        elif ch == "}" and brace_depth > 0:
            brace_depth -= 1

        buf.append(ch)
        if ch in "\n\r" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            flush()
        i += 1

    flush()
    return chunks


def _parse_top_level_decl_chunks(source: str) -> list[FuncDecl | ClassDecl | MethodDecl]:
    parser = build_top_level_decl_parser()
    chunks = _split_top_level_decls(source)
    decls: list[FuncDecl | ClassDecl | MethodDecl] = []
    for chunk in chunks:
        node = parser.parse(chunk)
        if not isinstance(node, Tree):
            raise ValueError("invalid top-level declaration parse result")
        decls.append(_parse_top_level_decl(node))
    return decls


def parse_source(source: str, module_name: str, parser: Lark | None = None) -> Program:
    p = parser or build_parser()
    contract_order, contract_exports = _extract_contract_exports(source, module_name)
    blocks = _extract_module_blocks(source, module_name)
    if blocks is not None:
        return _resolve_module_blocks(
            blocks,
            module_name=module_name,
            parser=p,
            contract_order=contract_order,
            contract_exports=contract_exports,
        )
    decls = _parse_top_level_decl_chunks(source)
    return Program(module_name=module_name, decls=decls)


def parse_file(path: Path, parser: Lark | None = None) -> Program:
    src = path.read_text(encoding="utf-8")
    return parse_source(src, module_name=path.name, parser=parser)


def iter_inputs(in_path: Path) -> list[Path]:
    if in_path.is_file():
        return [in_path]
    return sorted(p for p in in_path.glob("*.dmd") if p.is_file())
