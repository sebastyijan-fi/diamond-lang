#!/usr/bin/env python3
"""Parse-check profile_v1 programs with a strict grammar."""

from __future__ import annotations

from pathlib import Path
from lark import Lark

GRAMMAR = r"""
start: decl+

decl: IDENT tool_header? "(" [param ("," param)*] ")" ">" type "=" expr
tool_header: "^" "(" IDENT ("," IDENT)* ")"
param: IDENT ":" type

type: IDENT
    | "[" type "]"
    | "{" [type_field ("," type_field)*] "}"
type_field: IDENT ":" type

?expr: cond
?cond: match ("?" expr ":" expr)?
?match: or_expr ("~" pattern ":" expr)*
pattern: "_" | literal | IDENT

?or_expr: and_expr ("|" and_expr)*
?and_expr: cmp_expr ("&" cmp_expr)*
?cmp_expr: add_expr (("=="|"!="|"<"|"<="|">"|">=") add_expr)*
?add_expr: mul_expr (("+"|"-"|"$") mul_expr)*
?mul_expr: pow_expr (("*"|"/"|"%") pow_expr)*
?pow_expr: map_expr ("^" map_expr)*

?map_expr: range_expr ("#" IDENT ":" expr)?
?range_expr: unary_expr (".." unary_expr)?

?unary_expr: "-" unary_expr -> neg
           | postfix

?postfix: primary post_op*
?post_op: "(" [expr ("," expr)*] ")"   -> call
        | "." IDENT                       -> member
        | "[" slice_or_index "]"         -> index
        | "{" [map_item ("," map_item)*] "}" -> patch

?slice_or_index: expr
               | [expr] ":" [expr]

?primary: IDENT
        | literal
        | "(" expr ")"

?literal: NUMBER
        | STRING
        | "t"
        | "f"
        | list_lit
        | map_lit

list_lit: "[" [expr ("," expr)*] "]"
map_lit: "{" [map_item ("," map_item)*] "}"
map_item: (IDENT|STRING) ":" expr

IDENT: /[A-Za-z_][A-Za-z0-9_]*/
NUMBER: /\d+(\.\d+)?/
STRING: /"([^"\\]|\\.)*"/

%import common.WS_INLINE
%import common.NEWLINE
%ignore WS_INLINE
%ignore NEWLINE
"""


def main() -> int:
    parser = Lark(GRAMMAR, parser="lalr", start="start")
    base = Path("docs/decisions/profile_v1/programs")
    files = sorted(base.glob("*.dmd"))
    if not files:
        print("no profile_v1 programs found")
        return 1

    ok = 0
    for path in files:
        src = path.read_text(encoding="utf-8")
        try:
            parser.parse(src)
            print(f"ok {path.name}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"fail {path.name}: {exc}")
            return 2

    print(f"parsed {ok}/{len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
