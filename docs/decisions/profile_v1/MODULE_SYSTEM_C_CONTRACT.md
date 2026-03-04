# Module System C-contract (D10 Extension Candidate)

Purpose: context-window mode for large codebases using generated interface contracts.

## Rules (Measured)

The text below is the measured rules payload for `spec_tokens`.

```text
Grammar stays @b[cap:..]{decl*}.
Contract lines: //@b exposes f(sig)>T,...
Chunk context = dependency contracts + one active block.
Bare names are local; cross-block refs stay b.name; _private stays hidden.
If a block and contract both exist, symbols must match.
If only contracts exist for a dependency block, transpiler emits external stubs.
```

## Behavior Notes

- No new parser/IR syntax is required; contracts are metadata comments.
- `//@block exposes ...` declares callable interface only (signatures + optional caps).
- Contract mode is for generation/edit orchestration under context pressure.
- Full compile still uses complete `@block` sources for executable parity; contract-only deps compile to explicit runtime stubs.

## Minimal Example (3 Blocks, Active Chunk)

```text
//@types exposes to_i(s:S)>I
//@store exposes get(id:I)>S

@app{
  handle(id:S)>S=store.get(types.to_i(id))
}
```

Dependency contracts shown to `@app`:
- `types`
- `store`
