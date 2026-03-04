#!/usr/bin/env python3
"""Regression tests for D10 B-core inline module parsing/resolution."""

from __future__ import annotations

from diamond_ir import CallExpr, ListExpr, NameExpr, StringExpr
from parse_to_ir import parse_source


def test_multiblock_resolution_and_mangling() -> None:
    src = """@a{
f(x:I)>I=x
g(y:I)>I=f(y)
}
@b{
h(z:I)>I=a.g(z)
}
"""
    prog = parse_source(src, module_name="mod_ok.dmd")
    names = [d.name for d in prog.decls]
    if names != ["a__f", "a__g", "b__h"]:
        raise AssertionError(f"unexpected declaration order/names: {names}")

    g_body = prog.decls[1].body
    if not isinstance(g_body, CallExpr) or not isinstance(g_body.func, NameExpr):
        raise AssertionError("expected call body for a__g")
    if g_body.func.name != "a__f":
        raise AssertionError(f"expected local resolution to a__f, got {g_body.func.name}")

    h_body = prog.decls[2].body
    if not isinstance(h_body, CallExpr) or not isinstance(h_body.func, NameExpr):
        raise AssertionError("expected call body for b__h")
    if h_body.func.name != "a__g":
        raise AssertionError(f"expected cross-block resolution to a__g, got {h_body.func.name}")


def test_block_caps_attached_to_decls() -> None:
    src = """@net[cap:net.connect,rng.uniform]{
f(x:I)>I=x
}
"""
    prog = parse_source(src, module_name="caps_ok.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    d = prog.decls[0]
    tool_set = set(d.tools)
    if "c" not in tool_set:
        raise AssertionError(f"expected 'c' marker in tools, got {d.tools}")
    if "net.connect" not in tool_set or "rng.uniform" not in tool_set:
        raise AssertionError(f"expected block capabilities in tools, got {d.tools}")


def test_private_symbol_blocked() -> None:
    src = """@a{
_x()>I=1
}
@b{
y()>I=a._x()
}
"""
    try:
        parse_source(src, module_name="private_fail.dmd")
    except ValueError as exc:
        if "private symbol access denied" not in str(exc):
            raise AssertionError(f"unexpected error: {exc}") from exc
    else:
        raise AssertionError("expected private symbol access error")


def test_missing_symbol_blocked() -> None:
    src = """@a{
x()>I=1
}
@b{
y()>I=a.nope()
}
"""
    try:
        parse_source(src, module_name="missing_fail.dmd")
    except ValueError as exc:
        if "missing symbol a.nope" not in str(exc):
            raise AssertionError(f"unexpected error: {exc}") from exc
    else:
        raise AssertionError("expected missing symbol error")


def test_unknown_block_qualifier_blocked() -> None:
    src = """@a{
x()>I=1
}
@b{
y()>I=z.x()
}
"""
    try:
        parse_source(src, module_name="unknown_block_fail.dmd")
    except ValueError as exc:
        if "unknown block qualifier 'z'" not in str(exc):
            raise AssertionError(f"unexpected error: {exc}") from exc
    else:
        raise AssertionError("expected unknown block qualifier error")


def test_block_dependency_order_topological() -> None:
    src = """@b{
h(z:I)>I=a.g(z)
}
@a{
g(y:I)>I=y+1
}
"""
    prog = parse_source(src, module_name="dep_order_ok.dmd")
    names = [d.name for d in prog.decls]
    if names != ["a__g", "b__h"]:
        raise AssertionError(f"expected dependency order a then b, got {names}")


def test_block_cycle_rejected() -> None:
    src = """@a{
f()>I=b.g()
}
@b{
g()>I=a.f()
}
"""
    try:
        parse_source(src, module_name="block_cycle_fail.dmd")
    except ValueError as exc:
        if "module block cycle detected" not in str(exc):
            raise AssertionError(f"unexpected error: {exc}") from exc
    else:
        raise AssertionError("expected module block cycle error")


def test_contract_comment_prefix_before_blocks() -> None:
    src = """//@types exposes to_i(s:S)>I
//@store exposes get(id:I)>S
@types{
to_i(s:S)>I=I(s)
}
@store{
get(id:I)>S=\"u\"+S(id)
}
@app{
handle(id:S)>S=store.get(types.to_i(id))
}
"""
    prog = parse_source(src, module_name="contract_prefix_ok.dmd")
    names = [d.name for d in prog.decls]
    if names != ["types__to_i", "store__get", "app__handle"]:
        raise AssertionError(f"unexpected declaration order/names: {names}")


def test_contract_external_stubs_emitted() -> None:
    src = """//@dep exposes get(k:S)>S
@app{
run(k:S)>S=dep.get(k)
}
"""
    prog = parse_source(src, module_name="contract_external_stub.dmd")
    names = [d.name for d in prog.decls]
    if names != ["app__run", "dep__get"]:
        raise AssertionError(f"unexpected declaration order/names: {names}")

    run_body = prog.decls[0].body
    if not isinstance(run_body, CallExpr) or not isinstance(run_body.func, NameExpr):
        raise AssertionError("expected call body for app__run")
    if run_body.func.name != "dep__get":
        raise AssertionError(f"expected dep__get call target, got {run_body.func.name}")

    dep_body = prog.decls[1].body
    if not isinstance(dep_body, CallExpr) or not isinstance(dep_body.func, NameExpr):
        raise AssertionError("expected call body for dep__get external stub")
    if dep_body.func.name != "ext":
        raise AssertionError(f"expected ext helper call in stub, got {dep_body.func.name}")
    if len(dep_body.args) != 2 or not isinstance(dep_body.args[0], StringExpr):
        raise AssertionError("expected ext(symbol,args) signature in stub body")
    if dep_body.args[0].value != "\"dep.get\"":
        raise AssertionError(f"unexpected stub symbol payload: {dep_body.args[0].value}")
    if not isinstance(dep_body.args[1], ListExpr):
        raise AssertionError("expected list payload for external stub args")


def main() -> int:
    tests = [
        ("multiblock_resolution_and_mangling", test_multiblock_resolution_and_mangling),
        ("block_caps_attached_to_decls", test_block_caps_attached_to_decls),
        ("private_symbol_blocked", test_private_symbol_blocked),
        ("missing_symbol_blocked", test_missing_symbol_blocked),
        ("unknown_block_qualifier_blocked", test_unknown_block_qualifier_blocked),
        ("block_dependency_order_topological", test_block_dependency_order_topological),
        ("block_cycle_rejected", test_block_cycle_rejected),
        ("contract_comment_prefix_before_blocks", test_contract_comment_prefix_before_blocks),
        ("contract_external_stubs_emitted", test_contract_external_stubs_emitted),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"module system regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
