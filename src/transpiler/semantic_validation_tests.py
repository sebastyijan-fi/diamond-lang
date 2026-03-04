#!/usr/bin/env python3
"""Regression checks for static semantic/type validation."""

from __future__ import annotations

from parse_to_ir import parse_source
from semantic_validate import validate_program_semantics


def _report(src: str):
    prog = parse_source(src, module_name="sem_tests.dmd")
    return validate_program_semantics(prog)


def test_fold_scope_ok() -> None:
    src = "f(a:[I])>[I]=fold(a,[],x,t,x+[t])"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"expected no errors, got {rep.errors}")


def test_return_type_mismatch() -> None:
    src = "f(x:S)>I=x"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch error")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_local_call_arity_mismatch() -> None:
    src = "g(x:I,y:I)>I=x+y\nf(x:I)>I=g(x)"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected call arity mismatch error")
    if not any("call arity mismatch for 'g'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_reraise_outside_handler() -> None:
    src = "f()>I=reraise"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected reraise placement error")
    if not any("reraise used outside try-catch handler" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_undefined_symbol() -> None:
    src = "f(x:I)>I=x+y"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected undefined symbol error")
    if not any("undefined symbol 'y'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_implicit_receiver_ok() -> None:
    src = "$C(x:O){{}}\n.C.m()>O=#.x"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_explicit_self_rejected() -> None:
    src = "$C(x:O){{}}\n.C.m(self:O)>O=#.x"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected explicit self rejection")
    if not any("receiver is implicit; remove explicit self parameter" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_class_initializer_forward_reference_rejected() -> None:
    src = "$C(x:I){{b:#.a,a:x}}"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected class forward-reference error")
    if not any("references 'a' before initialization" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_unknown_self_member_rejected() -> None:
    src = "$C(x:I){{}}\n.C.m()>I=#.z"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected unknown self member error")
    if not any("unknown self member 'z'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_unknown_self_mutation_rejected() -> None:
    src = "$C(x:O){{}}\n.C.m()>O=#{z:1}"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected unknown self mutation error")
    if not any("invalid self mutation of unknown field 'z'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_declared_self_mutation_allowed() -> None:
    src = "$C(x:I){{}}\n.C.m()>M=#{x:1}"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_self_call_arity_mismatch_rejected() -> None:
    src = "$C(x:I){{}}\n.C.a(n:I)>I=n\n.C.b()>I=#.a()"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected self method arity mismatch error")
    if not any("call arity mismatch for method '#.a'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_field_called_as_method_rejected() -> None:
    src = "$C(x:I){{}}\n.C.b()>I=#.x()"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected field-called-as-method error")
    if not any("is a field and cannot be called as method" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_self_call_arg_type_mismatch_rejected() -> None:
    src = '$C(x:I){{}}\n.C.a(n:I)>I=n\n.C.b()>I=#.a("s")'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected self method arg type mismatch error")
    if not any("arg 1 of method '#.a'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_self_call_return_type_propagates() -> None:
    src = '$C(x:I){{}}\n.C.a()>S="s"\n.C.b()>I=#.a()'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch propagated from self method call")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_self_field_header_type_propagates() -> None:
    src = "$C(x:I){{}}\n.C.m()>S=#.x"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected header field type propagation mismatch")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_self_field_default_type_propagates() -> None:
    src = "$C(x:I){{y:#.x+1}}\n.C.m()>S=#.y"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected default field type propagation mismatch")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_self_field_default_type_ok() -> None:
    src = "$C(x:I){{y:#.x+1}}\n.C.m()>I=#.y"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_nominal_method_call_arity_mismatch_rejected() -> None:
    src = "$C(x:I){{}}\n.C.a(n:I)>I=n\nf(c:C)>I=c.a()"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected nominal method arity mismatch")
    if not any("call arity mismatch for method 'C.a'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_nominal_method_call_arg_type_mismatch_rejected() -> None:
    src = '$C(x:I){{}}\n.C.a(n:I)>I=n\nf(c:C)>I=c.a("s")'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected nominal method arg type mismatch")
    if not any("arg 1 of method 'C.a'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_nominal_method_call_return_type_propagates() -> None:
    src = '$C(x:I){{}}\n.C.a()>S="s"\nf(c:C)>I=c.a()'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected nominal method return type mismatch")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_nominal_unknown_member_rejected() -> None:
    src = "$C(x:I){{}}\nf(c:C)>I=c.zz"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected nominal unknown member error")
    if not any("unknown member 'C.zz'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_nominal_field_called_as_method_rejected() -> None:
    src = "$C(x:I){{}}\nf(c:C)>I=c.x()"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected nominal field-called-as-method error")
    if not any("member 'C.x' is a field and cannot be called as method" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_nominal_assignment_exact_type_ok() -> None:
    src = "$A(x:I){{}}\nf(a:A)>A=a"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_nominal_assignment_mismatch_rejected() -> None:
    src = "$A(x:I){{}}\n$B(x:I){{}}\nf(a:A)>B=a"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected nominal assignment mismatch")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_record_structural_assignable_ok() -> None:
    src = "f(x:{a:I,b:I})>{a:I}=x"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_record_structural_mismatch_rejected() -> None:
    src = "f(x:{a:S})>{a:I}=x"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected structural record mismatch")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_single_return_record_payload_ok() -> None:
    src = 'f()>{a:I,b:S}={a:1,b:"x"}'
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_function_overloading_rejected_duplicate_name() -> None:
    src = "f(x:I)>I=x\nf(x:S)>S=x"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected duplicate declaration error for function overloading")
    if not any("duplicate declaration 'f'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_method_overloading_rejected_duplicate_name() -> None:
    src = "$C(x:I){{}}\n.C.a(n:I)>I=n\n.C.a(s:S)>S=s"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected duplicate declaration error for method overloading")
    if not any("duplicate declaration 'C__a'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_json_loads_arg_type_mismatch_rejected() -> None:
    src = "f()>O=jdec(1)"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected jdec arg type mismatch")
    if not any("builtin 'jdec' arg 1" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_json_dumps_return_type_propagates() -> None:
    src = "f()>I=jenc({a:1})"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected jenc return type mismatch")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_date_builtin_return_type_propagates() -> None:
    src = "f()>I=dtd(2024,2,9)"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected dtd return type mismatch")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_tzutc_arity_mismatch_rejected() -> None:
    src = "f()>S=tzutc(1)"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected tzutc arity mismatch")
    if not any("call arity mismatch for builtin 'tzutc'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_ibase_arg_type_mismatch_rejected() -> None:
    src = 'f()>I=ibase("ff","16")'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected ibase arg type mismatch")
    if not any("builtin 'ibase' arg 2" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_datetime_builtins_ok() -> None:
    src = "f()>S=dtt(2024,2,9,10,11,12,13000,tzutc())"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_division_by_zero_literal_rejected() -> None:
    src = "f(x:I)>I=x/0"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected division by zero literal error")
    if not any("division by zero literal" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_modulo_by_zero_literal_rejected() -> None:
    src = "f(x:I)>I=x%0"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected modulo by zero literal error")
    if not any("modulo by zero literal" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_index_oob_list_literal_rejected() -> None:
    src = "f()>I=[1,2][9]"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected list literal index oob error")
    if not any("index out of bounds for list literal" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_index_oob_string_literal_rejected() -> None:
    src = 'f()>S="ab"[9]'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected string literal index oob error")
    if not any("index out of bounds for string literal" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_match_without_fallback_is_rejected() -> None:
    src = "f(x:I)>I=x~1:1~2:2"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected match exhaustiveness error")
    if not any("match expression must include a wildcard or capture arm for exhaustiveness" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_match_duplicate_literal_pattern_rejected() -> None:
    src = "f(x:I)>I=x~1:1~1:2~_:3"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected duplicate match pattern error")
    if not any("duplicate match literal pattern 'num:1'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_match_with_wildcard_passes() -> None:
    src = "f(x:I)>I=x~1:1~_:0"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_match_capture_passes() -> None:
    src = "f(x:I)>I=x~1:1~v:v"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_match_capture_expression_uses_binding() -> None:
    src = "f(x:I)>I=x~0:0~v:v+1"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_unknown_type_accepted_as_top() -> None:
    src = 'f(x:Unknown)>I=x'
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_void_type_accepted_as_unit() -> None:
    src = "f()>Void=none"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_never_parameter_assignable_to_return() -> None:
    src = "f(x:Never)>I=x"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_never_return_rejects_concrete_value() -> None:
    src = "f()>Never=1"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch for Never")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_non_null_return_rejects_none() -> None:
    src = "f()>I=none"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch for non-null return")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_non_null_parameter_rejects_none_argument() -> None:
    src = "g(x:I)>I=x\nf()>I=g(none)"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected arg mismatch for non-null parameter")
    if not any("arg 1 of 'g'" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_top_type_accepts_none() -> None:
    src = "f()>O=none"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_byte_in_range_literal_accepted() -> None:
    src = "f()>Byte=255"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_byte_out_of_range_literal_rejected() -> None:
    src = "f()>Byte=256"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch for Byte")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_bytes_list_literal_accepted() -> None:
    src = "f()>Bytes=[1,2,3]"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_bytes_rejects_string_literal() -> None:
    src = 'f()>Bytes="abc"'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch for Bytes")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_bytes_rejects_out_of_range_element() -> None:
    src = "f()>Bytes=[1,256]"
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch for Bytes element range")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_unsigned_integer_alias_accepted() -> None:
    src = "f(x:UInt)>I=x"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_pointer_sized_integer_alias_accepted() -> None:
    src = "f(x:usize)>I=x"
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_char_scalar_alias_accepts_single_codepoint() -> None:
    src = 'f()>Char="a"'
    rep = _report(src)
    if rep.errors:
        raise AssertionError(f"unexpected errors: {rep.errors}")


def test_char_scalar_alias_rejects_multi_codepoint_string() -> None:
    src = 'f()>Char="ab"'
    rep = _report(src)
    if not rep.errors:
        raise AssertionError("expected return type mismatch for Char")
    if not any("return type mismatch" in e for e in rep.errors):
        raise AssertionError(f"unexpected errors: {rep.errors}")


def main() -> int:
    tests = [
        ("fold_scope_ok", test_fold_scope_ok),
        ("return_type_mismatch", test_return_type_mismatch),
        ("local_call_arity_mismatch", test_local_call_arity_mismatch),
        ("reraise_outside_handler", test_reraise_outside_handler),
        ("undefined_symbol", test_undefined_symbol),
        ("method_implicit_receiver_ok", test_method_implicit_receiver_ok),
        ("method_explicit_self_rejected", test_method_explicit_self_rejected),
        ("class_initializer_forward_reference_rejected", test_class_initializer_forward_reference_rejected),
        ("method_unknown_self_member_rejected", test_method_unknown_self_member_rejected),
        ("method_unknown_self_mutation_rejected", test_method_unknown_self_mutation_rejected),
        ("method_declared_self_mutation_allowed", test_method_declared_self_mutation_allowed),
        ("method_self_call_arity_mismatch_rejected", test_method_self_call_arity_mismatch_rejected),
        ("method_field_called_as_method_rejected", test_method_field_called_as_method_rejected),
        ("method_self_call_arg_type_mismatch_rejected", test_method_self_call_arg_type_mismatch_rejected),
        ("method_self_call_return_type_propagates", test_method_self_call_return_type_propagates),
        ("method_self_field_header_type_propagates", test_method_self_field_header_type_propagates),
        ("method_self_field_default_type_propagates", test_method_self_field_default_type_propagates),
        ("method_self_field_default_type_ok", test_method_self_field_default_type_ok),
        ("nominal_method_call_arity_mismatch_rejected", test_nominal_method_call_arity_mismatch_rejected),
        ("nominal_method_call_arg_type_mismatch_rejected", test_nominal_method_call_arg_type_mismatch_rejected),
        ("nominal_method_call_return_type_propagates", test_nominal_method_call_return_type_propagates),
        ("nominal_unknown_member_rejected", test_nominal_unknown_member_rejected),
        ("nominal_field_called_as_method_rejected", test_nominal_field_called_as_method_rejected),
        ("nominal_assignment_exact_type_ok", test_nominal_assignment_exact_type_ok),
        ("nominal_assignment_mismatch_rejected", test_nominal_assignment_mismatch_rejected),
        ("record_structural_assignable_ok", test_record_structural_assignable_ok),
        ("record_structural_mismatch_rejected", test_record_structural_mismatch_rejected),
        ("single_return_record_payload_ok", test_single_return_record_payload_ok),
        ("function_overloading_rejected_duplicate_name", test_function_overloading_rejected_duplicate_name),
        ("method_overloading_rejected_duplicate_name", test_method_overloading_rejected_duplicate_name),
        ("json_loads_arg_type_mismatch_rejected", test_json_loads_arg_type_mismatch_rejected),
        ("json_dumps_return_type_propagates", test_json_dumps_return_type_propagates),
        ("date_builtin_return_type_propagates", test_date_builtin_return_type_propagates),
        ("tzutc_arity_mismatch_rejected", test_tzutc_arity_mismatch_rejected),
        ("ibase_arg_type_mismatch_rejected", test_ibase_arg_type_mismatch_rejected),
        ("datetime_builtins_ok", test_datetime_builtins_ok),
        ("division_by_zero_literal_rejected", test_division_by_zero_literal_rejected),
        ("modulo_by_zero_literal_rejected", test_modulo_by_zero_literal_rejected),
        ("index_oob_list_literal_rejected", test_index_oob_list_literal_rejected),
        ("index_oob_string_literal_rejected", test_index_oob_string_literal_rejected),
        ("match_without_fallback_is_rejected", test_match_without_fallback_is_rejected),
        ("match_duplicate_literal_pattern_rejected", test_match_duplicate_literal_pattern_rejected),
        ("match_with_wildcard_passes", test_match_with_wildcard_passes),
        ("match_capture_passes", test_match_capture_passes),
        ("match_capture_expression_uses_binding", test_match_capture_expression_uses_binding),
        ("unknown_type_accepted_as_top", test_unknown_type_accepted_as_top),
        ("void_type_accepted_as_unit", test_void_type_accepted_as_unit),
        ("never_parameter_assignable_to_return", test_never_parameter_assignable_to_return),
        ("never_return_rejects_concrete_value", test_never_return_rejects_concrete_value),
        ("non_null_return_rejects_none", test_non_null_return_rejects_none),
        ("non_null_parameter_rejects_none_argument", test_non_null_parameter_rejects_none_argument),
        ("top_type_accepts_none", test_top_type_accepts_none),
        ("byte_in_range_literal_accepted", test_byte_in_range_literal_accepted),
        ("byte_out_of_range_literal_rejected", test_byte_out_of_range_literal_rejected),
        ("bytes_list_literal_accepted", test_bytes_list_literal_accepted),
        ("bytes_rejects_string_literal", test_bytes_rejects_string_literal),
        ("bytes_rejects_out_of_range_element", test_bytes_rejects_out_of_range_element),
        ("unsigned_integer_alias_accepted", test_unsigned_integer_alias_accepted),
        ("pointer_sized_integer_alias_accepted", test_pointer_sized_integer_alias_accepted),
        ("char_scalar_alias_accepts_single_codepoint", test_char_scalar_alias_accepts_single_codepoint),
        ("char_scalar_alias_rejects_multi_codepoint_string", test_char_scalar_alias_rejects_multi_codepoint_string),
    ]
    for name, fn in tests:
        fn()
        print(f"ok {name}")
    print(f"semantic validation regressions: {len(tests)}/{len(tests)} passing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
