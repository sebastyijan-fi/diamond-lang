# Module System B-core (D10 Candidate)

Purpose: minimal inline-only module structure for cold-start generation.

## Rules (Measured)

The text below is the measured rules payload for `spec_tokens`.

```text
@b[cap:c1,c2]{decl*}; cap optional: @b{decl*}.
Bare names resolve only inside the current block.
Cross-block refs must be qualified as b.name.
Decls export by default; names starting "_" are block-private.
No contracts, manifests, or file directives; blocks are inline only.
Transpiler builds a block table, resolves b.name, errors on missing or ambiguous refs.
Emit may flatten or split files; semantics must remain identical.
```

## Behavior Notes

- `@block` syntax: block id + optional capability list + declarations.
- Capability declaration: `cap:` list is metadata on the block scope only.
- Name visibility:
  - Local: bare names.
  - External: `block.symbol`.
  - Private: `_name` cannot be referenced from other blocks.
- Transpiler resolution:
  - Parse all blocks in one source.
  - Build global block/symbol table.
  - Resolve all qualified references.
  - Reject unresolved or ambiguous references.

## Minimal Example (3 Blocks, 2 Edges)

```text
@util[cap:cpu]{
  to_i(s:S)>I=I(s)
}

@store[cap:mem]{
  get(id:I)>S="u"+S(id)
}

@app[cap:net]{
  handle(id:S)>S=store.get(util.to_i(id))
}
```

Dependency edges:
- `app -> util`
- `app -> store`
