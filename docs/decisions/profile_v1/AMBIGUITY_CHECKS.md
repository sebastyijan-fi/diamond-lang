# Ambiguity Checks v1

Scope: profile constructs extracted from winning `C` syntax.

## Checks Per Construct

1. Function declaration

- Risk in raw C: implicit parameters (`h:S,S>...`) allow multiple variable-binding interpretations.
- v1 fix: explicit named params only (`h(m:S,p:S)>...`).
- Status: resolved with syntactic requirement.

2. Nested conditionals (`? :`)

- Risk: dangling else equivalent for nested ternaries.
- v1 rule: right-associative parse.
- Status: resolved by grammar precedence.

3. Match chain (`~pat:expr`)

- Risk: `~` could be interpreted as bitwise/logical operator.
- v1 rule: `~` only valid in match-chain production.
- Status: resolved by operator reservation.

4. Comprehension (`#v:expr`)

- Risk: `#` as generic binary operator vs binder.
- v1 rule: `#` only valid as binder after a source expression.
- Status: resolved by restricted production.

5. `:` collision

- Used by ternary, match-chain, map literals, and type annotations.
- v1 mitigation:
  - type `:` only in headers and typed param lists
  - map key `:` only inside `{}`
  - ternary `:` must follow `?` arm
  - match-chain `:` must follow `~pattern`
- Status: manageable with contextual grammar.

6. Slice/index brackets

- Risk: `x[a:b]` vs `x[i]`.
- v1 rule: dedicated `slice_or_index` grammar with optional endpoints.
- Status: resolved.

7. Tool-header inheritance

- Risk: omitted header on a declaration could be interpreted as either "no tools" or "same tools as previous declaration."
- v1 rule:
  - explicit header syntax is `name^(...)`.
  - missing header in a contiguous declaration group means inherit previous explicit header.
  - inheritance is lexical and forward-only.
- Status: resolved by deterministic declaration-order rule.

8. Single-use helper inlining

- Risk: inlining may alter meaning if helper bodies contain side effects or evaluation-order-sensitive operations.
- v1 rule:
  - allow inlining only for pure expression helpers (no external boundary effects).
  - preserve operator precedence with explicit parentheses in nested ternaries.
- Status: parse ambiguity unaffected; semantic safety constrained by purity rule.

9. Record patch vs map literal (`expr{...}`)

- Risk: `x{k:v}` could be confused with a standalone map literal `{k:v}`.
- v1 rule:
  - map literal is a `primary` form.
  - patch is a `post_op` form and only valid after a completed expression.
- Status: resolved by grammar position (`primary` vs `postfix post_op`).

10. Midpoint operator (`$`)

- Risk: interaction with arithmetic precedence and existing infix operators.
- v1 rule:
  - `$` is parsed in `add_expr` precedence level alongside `+` and `-`.
  - parse is left-associative and deterministic.
- Status: resolved by explicit precedence placement.

11. Postfix propagation + immediate index (`expr?[i]`)

- Risk: `?` can be ternary marker or propagation postfix.
- v1 rule:
  - `?[` (no whitespace between `?` and `[`) is a dedicated postfix propagate+index/slice form.
  - ternary remains `? ... : ...`.
  - if then-arm starts with list literal, write ternary as `x ? [..] : y` (space) or parenthesize.
- Status: resolved by token-priority + explicit postfix production.

12. Contract metadata comment lines before module blocks

- Risk: C-contract context headers can appear before `@block` starts and break module-block detection.
- v1 rule:
  - line comments use `//...` and are parser-ignored.
  - module extraction skips leading `//` comment lines before scanning for `@block`.
  - contract metadata form is `//@block exposes ...` (orchestration metadata only).
- Status: resolved for parseability; semantics remain metadata-only.

## Remaining Risks

- Semantic ambiguity from extremely short identifiers (`a,b,x,t`) is still possible at human level, but parse ambiguity is distinct and handled by grammar.
- Builtin function semantics (`fold`, `put`, `del`, `ln`) are not part of syntax ambiguity; they are runtime/spec concerns.

## Gate For Promotion

Profile stays provisional until:

- All 10 profile programs parse under one grammar.
- No parser conflicts in the chosen parser backend.
- No construct requires backtracking hacks that imply hidden ambiguity.
