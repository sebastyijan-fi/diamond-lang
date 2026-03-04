#!/usr/bin/env python3
"""Targeted parser regressions for known ambiguity edges."""

from __future__ import annotations

from diamond_ir import (
    ClassDecl,
    FuncDecl,
    IndexExpr,
    ListExpr,
    MemberExpr,
    MethodDecl,
    NameExpr,
    NumberExpr,
    PropagateExpr,
    PatternIdent,
    MatchExpr,
    SliceExpr,
    TernaryExpr,
)
from parse_to_ir import parse_source


def _single_body(src: str):
    prog = parse_source(src, module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    decl = prog.decls[0]
    if not isinstance(decl, FuncDecl):
        raise AssertionError(f"expected FuncDecl, got {type(decl).__name__}")
    return decl.body


def test_func_decl_parses() -> None:
    prog = parse_source("g(x:I)>I=x+1", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    if not isinstance(prog.decls[0], FuncDecl):
        raise AssertionError(f"expected FuncDecl, got {type(prog.decls[0]).__name__}")


def test_class_decl_parses() -> None:
    prog = parse_source("$Point(x:I,y:I){{\"tag\":\"p\"}}", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    d = prog.decls[0]
    if not isinstance(d, ClassDecl):
        raise AssertionError(f"expected ClassDecl, got {type(d).__name__}")
    if d.name != "Point":
        raise AssertionError(f"expected class name Point, got {d.name}")
    if [p.name for p in d.params] != ["x", "y"]:
        raise AssertionError(f"unexpected class params: {[p.name for p in d.params]}")


def test_multiline_class_body_parses() -> None:
    src = "$Point(x:I){\n{\"a\":1,\n\"b\":2}\n}"
    prog = parse_source(src, module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    if not isinstance(prog.decls[0], ClassDecl):
        raise AssertionError(f"expected ClassDecl, got {type(prog.decls[0]).__name__}")


def test_method_decl_parses() -> None:
    prog = parse_source(".Point.len()>I=#.x", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    d = prog.decls[0]
    if not isinstance(d, MethodDecl):
        raise AssertionError(f"expected MethodDecl, got {type(d).__name__}")
    if d.class_name != "Point":
        raise AssertionError(f"expected class_name Point, got {d.class_name}")
    if d.func_decl.name != "len":
        raise AssertionError(f"expected method name len, got {d.func_decl.name}")


def test_method_decl_with_tools_parses() -> None:
    prog = parse_source(".Point.len^(db)()>I=#.x", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    d = prog.decls[0]
    if not isinstance(d, MethodDecl):
        raise AssertionError(f"expected MethodDecl, got {type(d).__name__}")
    if d.func_decl.tools != ["db"]:
        raise AssertionError(f"expected method tool header ['db'], got {d.func_decl.tools}")


def test_adjacent_method_decls_parse() -> None:
    src = ".Point.a()>I=1\n.Point.b()>I=#.a()"
    prog = parse_source(src, module_name="parser_regressions.dmd")
    if len(prog.decls) != 2:
        raise AssertionError(f"expected 2 declarations, got {len(prog.decls)}")
    first = prog.decls[0]
    second = prog.decls[1]
    if not isinstance(first, MethodDecl) or not isinstance(second, MethodDecl):
        raise AssertionError(
            f"expected two MethodDecl entries, got {[type(d).__name__ for d in prog.decls]}"
        )
    if first.func_decl.name != "a" or second.func_decl.name != "b":
        raise AssertionError(
            f"expected method names ['a','b'], got {[first.func_decl.name, second.func_decl.name]}"
        )


def test_self_binder_member_parse() -> None:
    body = _single_body("g(self:O)>O=#.x")
    if not isinstance(body, MemberExpr):
        raise AssertionError(f"expected MemberExpr, got {type(body).__name__}")
    if not isinstance(body.obj, NameExpr) or body.obj.name != "self":
        raise AssertionError("expected self binder to parse as NameExpr('self')")
    if body.name != "x":
        raise AssertionError(f"expected member x, got {body.name}")


def test_propagate_index() -> None:
    body = _single_body("g(a:[I])>I=a?[0]")
    if not isinstance(body, IndexExpr):
        raise AssertionError(f"expected IndexExpr, got {type(body).__name__}")
    if not isinstance(body.obj, PropagateExpr):
        raise AssertionError(f"expected PropagateExpr object, got {type(body.obj).__name__}")
    if not isinstance(body.obj.expr, NameExpr) or body.obj.expr.name != "a":
        raise AssertionError("expected propagate base name 'a'")
    if not isinstance(body.index, NumberExpr) or body.index.value != "0":
        raise AssertionError("expected index 0")


def test_propagate_slice() -> None:
    body = _single_body("g(a:[I])>[I]=a?[1:3]")
    if not isinstance(body, SliceExpr):
        raise AssertionError(f"expected SliceExpr, got {type(body).__name__}")
    if not isinstance(body.obj, PropagateExpr):
        raise AssertionError(f"expected PropagateExpr object, got {type(body.obj).__name__}")
    if not isinstance(body.start, NumberExpr) or body.start.value != "1":
        raise AssertionError("expected slice start 1")
    if not isinstance(body.end, NumberExpr) or body.end.value != "3":
        raise AssertionError("expected slice end 3")


def test_ternary_unchanged() -> None:
    body = _single_body("g(x:I)>I=x?0:1")
    if not isinstance(body, TernaryExpr):
        raise AssertionError(f"expected TernaryExpr, got {type(body).__name__}")


def test_ternary_list_then_arm() -> None:
    body = _single_body("g(x:I)>I=x ? [1][0] : 0")
    if not isinstance(body, TernaryExpr):
        raise AssertionError(f"expected TernaryExpr, got {type(body).__name__}")
    if not isinstance(body.then_expr, IndexExpr):
        raise AssertionError("expected then-arm index expression")
    if not isinstance(body.then_expr.obj, ListExpr):
        raise AssertionError("expected list literal in then-arm")


def test_match_capture_pattern_parses() -> None:
    body = _single_body("g(x:I)>I=x~1:1~v:v")
    if not isinstance(body, MatchExpr):
        raise AssertionError(f"expected MatchExpr, got {type(body).__name__}")
    if len(body.arms) != 2:
        raise AssertionError(f"expected 2 match arms, got {len(body.arms)}")
    if not isinstance(body.arms[1].pattern, PatternIdent):
        raise AssertionError(
            f"expected PatternIdent in second arm, got {type(body.arms[1].pattern).__name__}"
        )
    if body.arms[1].pattern.name != "v":
        raise AssertionError(f"expected capture name 'v', got {body.arms[1].pattern.name!r}")
    if not isinstance(body.arms[1].expr, NameExpr) or body.arms[1].expr.name != "v":
        raise AssertionError("expected capture name to be used inside match arm expression")


def test_line_comment_ignored() -> None:
    base = _single_body("h(x:I)>I=x+1")
    body = _single_body("// contract metadata\nh(x:I)>I=x+1")
    if type(body) is not type(base):
        raise AssertionError("line comment should be ignored by parser")


def test_unknown_type_annotation_parses() -> None:
    prog = parse_source("g(x:Unknown, y:top)>I=x", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    if not isinstance(prog.decls[0], FuncDecl):
        raise AssertionError(f"expected FuncDecl, got {type(prog.decls[0]).__name__}")


def test_unit_void_never_type_annotations_parse() -> None:
    prog = parse_source("g(a:V,b:Void,c:Unit)>Never=a", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    if not isinstance(prog.decls[0], FuncDecl):
        raise AssertionError(f"expected FuncDecl, got {type(prog.decls[0]).__name__}")


def test_byte_bytes_type_annotations_parse() -> None:
    prog = parse_source("g(a:Byte,b:Bytes,c:u8)>Bytes=b", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    if not isinstance(prog.decls[0], FuncDecl):
        raise AssertionError(f"expected FuncDecl, got {type(prog.decls[0]).__name__}")


def test_type_alias_declaration_rejected() -> None:
    src = "type UserId=I"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected type alias declaration to be rejected in v1")


def test_newtype_declaration_rejected() -> None:
    src = "newtype UserId:I"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected newtype declaration to be rejected in v1")


def test_multi_return_function_signature_rejected() -> None:
    src = "f()>I,S=1"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected multi-return function signature to be rejected in v1")


def test_multi_return_method_signature_rejected() -> None:
    src = "$C(){{}}\n.C.m()>I,S=1"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected multi-return method signature to be rejected in v1")


def test_enum_declaration_rejected() -> None:
    src = "enum Color{Red,Blue}"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected enum declaration to be rejected in v1")


def test_union_type_annotation_rejected() -> None:
    src = "f(x:I|S)>I=1"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected union type annotation to be rejected in v1")


def test_generic_function_declaration_rejected() -> None:
    src = "f[T](x:T)>T=x"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected generic function declaration to be rejected in v1")


def test_generic_type_parameter_annotation_rejected() -> None:
    src = "f(x:Map[S,I])>I=1"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected generic type parameter annotation to be rejected in v1")


def test_unsigned_pointer_char_type_annotations_parse() -> None:
    prog = parse_source("g(a:UInt,b:usize,c:Char)>I=a", module_name="parser_regressions.dmd")
    if len(prog.decls) != 1:
        raise AssertionError(f"expected 1 declaration, got {len(prog.decls)}")
    if not isinstance(prog.decls[0], FuncDecl):
        raise AssertionError(f"expected FuncDecl, got {type(prog.decls[0]).__name__}")


def test_macro_declaration_rejected() -> None:
    src = "macro m(x)=x"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected macro declaration to be rejected in v1")


def test_compile_time_eval_syntax_rejected() -> None:
    src = "f()>I=comptime{1}"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected compile-time eval syntax to be rejected in v1")


def test_reflection_codegen_syntax_rejected() -> None:
    src = "@derive(eq)\nf()>I=1"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected reflection/codegen annotation syntax to be rejected in v1")


def test_effect_system_syntax_rejected() -> None:
    src = "effect IO"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected effect-system syntax to be rejected in v1")


def test_inheritance_extends_syntax_rejected() -> None:
    src = "$A(x:I){{}}\n$B(y:I) extends A {{}}"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected inheritance syntax to be rejected in v1")


def test_trait_interface_syntax_rejected() -> None:
    src = "trait T{x()>I}"
    try:
        parse_source(src, module_name="parser_regressions.dmd")
    except Exception:
        return
    raise AssertionError("expected trait/interface syntax to be rejected in v1")


def main() -> int:
    tests = [
        ("func_decl_parses", test_func_decl_parses),
        ("class_decl_parses", test_class_decl_parses),
        ("multiline_class_body_parses", test_multiline_class_body_parses),
        ("method_decl_parses", test_method_decl_parses),
        ("method_decl_with_tools_parses", test_method_decl_with_tools_parses),
        ("adjacent_method_decls_parse", test_adjacent_method_decls_parse),
        ("self_binder_member_parse", test_self_binder_member_parse),
        ("propagate_index", test_propagate_index),
        ("propagate_slice", test_propagate_slice),
        ("ternary_unchanged", test_ternary_unchanged),
        ("ternary_list_then_arm", test_ternary_list_then_arm),
        ("line_comment_ignored", test_line_comment_ignored),
        ("match_capture_pattern_parses", test_match_capture_pattern_parses),
        ("unknown_type_annotation_parses", test_unknown_type_annotation_parses),
        ("unit_void_never_type_annotations_parse", test_unit_void_never_type_annotations_parse),
        ("byte_bytes_type_annotations_parse", test_byte_bytes_type_annotations_parse),
        ("type_alias_declaration_rejected", test_type_alias_declaration_rejected),
        ("newtype_declaration_rejected", test_newtype_declaration_rejected),
        ("multi_return_function_signature_rejected", test_multi_return_function_signature_rejected),
        ("multi_return_method_signature_rejected", test_multi_return_method_signature_rejected),
        ("enum_declaration_rejected", test_enum_declaration_rejected),
        ("union_type_annotation_rejected", test_union_type_annotation_rejected),
        ("generic_function_declaration_rejected", test_generic_function_declaration_rejected),
        ("generic_type_parameter_annotation_rejected", test_generic_type_parameter_annotation_rejected),
        ("unsigned_pointer_char_type_annotations_parse", test_unsigned_pointer_char_type_annotations_parse),
        ("macro_declaration_rejected", test_macro_declaration_rejected),
        ("compile_time_eval_syntax_rejected", test_compile_time_eval_syntax_rejected),
        ("reflection_codegen_syntax_rejected", test_reflection_codegen_syntax_rejected),
        ("effect_system_syntax_rejected", test_effect_system_syntax_rejected),
        ("inheritance_extends_syntax_rejected", test_inheritance_extends_syntax_rejected),
        ("trait_interface_syntax_rejected", test_trait_interface_syntax_rejected),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"parser regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
