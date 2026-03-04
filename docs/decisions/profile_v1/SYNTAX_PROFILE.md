# Diamond Provisional Syntax Profile v1

Basis: extracted from the 5 winning `C` candidates (`01, 06, 07, 10, 16`) and then minimally adjusted for parse clarity.

## Core Rules

1. Program unit

- A program is one or more function declarations.
- Declaration form:

```txt
name(p1:T1,p2:T2,... )>R=expr
```

2. Expressions are primary

- Function bodies are single expressions.
- Branching uses inline conditional:

```txt
cond?then_expr:else_expr
```

3. Pattern routing (multi-branch)

- Match-chain form:

```txt
value~pat1:expr1~pat2:expr2~_:default
```

- `_` is wildcard fallback.

4. Iteration/mapping

- Comprehension-style map:

```txt
src#v:expr
```

- Range source:

```txt
a..b
```

5. Types

- Single-token style types dominate current winners: `I`, `S`, `B`, `M`, `O`, `R`.
- List type: `[T]`.

6. Data literals

- List: `[e1,e2,...]`
- Map/record literal: `{k:v,...}`
- Booleans: `t`, `f`

7. Access/calls

- Field: `x.k`
- Index/slice: `x[i]`, `x[a:b]`, `x[:b]`, `x[a:]`
- Call: `f(a,b,c)`

8. Operators

- Arithmetic: `+ - * / % ^`
- Compare: `== != < <= > >=`
- Boolean: `& |`
- Midpoint infix (v4 candidate): `$`
  - `a$b` means integer midpoint of `a` and `b` (floor semantics).
  - Example: `a[l$r]` in binary-search style index updates.

9. Record patch (v4 candidate)

- Postfix patch form:

```txt
expr{k:v,...}
```

- Semantics: copy `expr` record/map and override listed fields.
- Example: `s{m:put(s.m,k,v)}`.

10. Math intrinsics (v4 candidate)

- `l(x)` and `r(x)` are half-split intrinsics used in divide-and-conquer forms.
  - Intended usage: `ms(l(a))`, `ms(r(a))`.

## Minimal Clarifications Added For v1

These are profile constraints to reduce ambiguity while preserving measured density:

- Parameters are explicit and named in function headers.
  - Raw C examples had implicit/free variables; this is disallowed.
- `~` is reserved for match-chain only (not generic infix operator).
- `#` is reserved for comprehension binding (`src#v:expr`).
- `? :` is right-associative.
- Tool-layer header form is:

```txt
name^(c,t,b)(p1:T1,...)>R=expr
```

- Tool-header inheritance rule:
  - In a contiguous declaration group, omitted tool headers inherit the most recent explicit tool header.
  - Inheritance applies only to subsequent declarations in the same group.
  - A new explicit header resets the inherited header for following declarations.

## Canonical Program Set (v1)

See `programs/` for the first 10 unified-profile programs:

- `01_fizzbuzz.dmd`
- `04_url_router.dmd`
- `06_http_handler_routing.dmd`
- `07_key_value_store_memory.dmd`
- `08_csv_parser.dmd`
- `09_binary_search.dmd`
- `10_merge_sort.dmd`
- `11_stack.dmd`
- `15_event_emitter.dmd`
- `16_retry_exponential_backoff.dmd`
