"""Shared Diamond profile grammar for transpiler backends.

Note: booleans are `true`/`false` here to avoid collisions with single-char
identifier-heavy Diamond style (e.g. `t` loop/item variables).
"""

DIAMOND_GRAMMAR = r"""
start: top_level_decl+

?top_level_decl: func_decl | class_decl | method_decl | decorator_decl
func_decl: IDENT tool_header? "(" [param ("," param)*] ")" ">" type "=" expr
class_decl: CLASS_SIGIL IDENT "(" [param ("," param)*] ")" "{" expr "}"
method_decl: "." IDENT "." IDENT tool_header? "(" [param ("," param)*] ")" ">" type "=" expr
decorator_decl: "@" expr "\n" top_level_decl
tool_header: "^" "(" IDENT ("," IDENT)* ")"
param: IDENT ":" type

type: IDENT
    | "[" type "]"
    | "{" [type_field ("," type_field)*] "}"
type_field: IDENT ":" type

?expr: try_catch
?try_catch: TRY "(" expr "," IDENT ":" expr ")" -> try_catch
          | seq
?seq: cond (SEMI cond)*
?cond: match (QMARK expr ":" expr)?
?match: or_expr match_arm*
match_arm: "~" pattern ":" cond_no_match
?cond_no_match: or_expr (QMARK expr ":" expr)?
pattern: "_" | literal | IDENT

?or_expr: and_expr (OR_OP and_expr)*
?and_expr: cmp_expr (AND_OP cmp_expr)*
?cmp_expr: add_expr (CMP_OP add_expr)*
?add_expr: mul_expr (ADD_OP mul_expr)*
?mul_expr: pow_expr (MUL_OP pow_expr)*
?pow_expr: map_expr (POW_OP map_expr)*

?map_expr: range_expr (MAP_BIND_OP IDENT ":" expr)?
?range_expr: unary_expr (RANGE_OP unary_expr)?

?unary_expr: "-" unary_expr -> neg
           | RERAISE        -> reraise
           | postfix

?postfix: primary post_op*
?post_op: "(" [expr ("," expr)*] ")"   -> call
        | "." IDENT                       -> member
        | PROP_INDEX_QMARK "[" slice_or_index "]" -> propagate_index
        | "[" slice_or_index "]"         -> index
        | "{" [map_item ("," map_item)*] "}" -> patch
        | PROP_QMARK                      -> propagate

?slice_or_index: expr
               | [expr] ":" [expr]

?primary: ISEXC "(" expr "," expr ("," expr)* ")" -> exc_match
        | IDENT
        | MAP_BIND_OP                     -> self_ref
        | literal
        | "(" expr ")"

?literal: NUMBER
        | STRING
        | TRUE
        | FALSE
        | list_lit
        | map_lit

list_lit: "[" [expr ("," expr)*] "]"
map_lit: "{" [map_item ("," map_item)*] "}"
map_item: (IDENT|STRING) ":" expr

IDENT: /[A-Za-z_][A-Za-z0-9_]*/
NUMBER: /\d+(\.\d+)?/
STRING: /"([^"\\]|\\.)*"/
CLASS_SIGIL: "$"
TRUE: "true"
FALSE: "false"
TRY: "try"
RERAISE: "reraise"
ISEXC: "isexc"
LINE_COMMENT: /\/\/[^\n\r]*/

OR_OP: "|"
AND_OP: "&"
CMP_OP: "=="|"!="|"<="|">="|"<"|">"
ADD_OP: "+"|"-"|"$"
MUL_OP: "*"|"/"|"%"
POW_OP: "^"
MAP_BIND_OP: "#"
RANGE_OP: ".."
# Dedicated postfix propagation+index form.
# The bracket content is intentionally limited to non-nested `[]` to avoid
# stealing ternary forms like `x?[a[0]]+...:...`.
PROP_INDEX_QMARK.3: /\?(?=\[[^\[\]\n\r]*\](?=\s*([+*%&|^)=\]},~.;.]|\/|\n|\r|$)))/
PROP_QMARK.2: /\?(?=\s*(?::|[+*%&|^)=\]},~.;.]|\/|\n|\r|$))/
QMARK.1: "?"
SEMI: ";"

%import common.WS_INLINE
%import common.NEWLINE
%ignore WS_INLINE
%ignore NEWLINE
%ignore LINE_COMMENT
"""
