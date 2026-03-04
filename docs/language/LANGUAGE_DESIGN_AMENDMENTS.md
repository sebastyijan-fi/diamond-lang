# Diamond Design Amendments

**Insights extracted from tokenizer research. These amend docs/language/LANGUAGE_DESIGN.md.**

Companion:
- `docs/language/LANGUAGE_CONSTRUCT_TOOL_FRAMEWORK.md` (construct-level semantic+tool fusion and budget model)

---

## Amendment 1: Tokenizer Profiles

Diamond's grammar is stable. The surface spellings are not.

Instead of locking Diamond to one tokenizer's optimal encodings, the language separates two layers:

```
Core grammar:  fixed EBNF, defines structure and semantics
Surface profile:  swappable mapping of abstract operators -> concrete spellings
```

A surface profile is a JSON file that maps every keyword and operator to its token-cheapest spelling for a specific tokenizer:

```json
{
  "profile": "qwen3-8b",
  "tokenizer": "Qwen/Qwen3-8B",
  "mappings": {
    "FN_DEF": "fn",
    "LET": "let",
    "IF": "if",
    "ELSE": "else",
    "CASE": "case",
    "ARROW": "->",
    "RESULT_OK": "ok",
    "RESULT_ERR": "err",
    "PROPAGATE": "?",
    "COMMENT": "#",
    "BLOCK_OPEN": "{",
    "BLOCK_CLOSE": "}"
  }
}
```

A different profile for a different tokenizer might map `FN_DEF` to `def` or `f` or `:` - whatever measures cheapest. The grammar doesn't change. The parser accepts any valid profile. The transpiler works regardless.

**Why this matters for ingestion:** When Diamond projects appear on GitHub, the crawler doesn't need to know about profiles. The code is valid Diamond regardless of which profile emitted it. But when optimizing for a specific model, the profile ensures optimal encoding.

**Action:** Add profile generation to the design pipeline. After running tokenbench on a tokenizer, automatically generate a profile by testing all candidate spellings per operator and selecting the cheapest.

---

## Amendment 2: Compiler-Driven Token-Minimizing Renamer

Diamond's compiler includes a pass that renames all identifiers to minimize token count under the target tokenizer.

This is not "use short names." It is context-aware optimization:

- BPE tokens can include leading whitespace (documented for Qwen: `" token"` is one token)
- An identifier at the start of a line tokenizes differently than after a space
- An identifier followed by `(` might merge differently than one followed by `.`
- The cheapest name for a variable depends on its position in the token stream

The renamer:
1. Parses the Diamond AST
2. For each scope, enumerates candidate names (a, b, c, ..., aa, ab, ...)
3. For each candidate, simulates the token stream in context
4. Selects the name that produces the fewest total tokens
5. Emits the renamed Diamond source

The human (or upstream LLM) writes semantic names. The renamer compresses them. Round-trip is maintained through a name map in metadata.

**Action:** Build the renamer as a standalone pass. Test on the 20 benchmark programs. Measure additional token savings on top of syntax compression.

---

## Amendment 3: Whitespace Hypothesis Test

Current assumption: denser = fewer tokens.
Challenge: BPE tokenizers have learned merges over common whitespace patterns.

Common indentation patterns like `\n    ` (newline + 4 spaces) may be single tokens in the Qwen vocabulary. If so, removing whitespace breaks those merges and could *increase* token count.

**Test required:** Take the winning C candidates and create two variants:
- C-dense: no unnecessary whitespace (current approach)
- C-formatted: standard indentation with newlines

Tokenize both. If C-formatted is cheaper or equivalent, whitespace elimination is not a universal win and the design should preserve some formatting.

**Action:** Add to the next measurement batch. This is a P0 test because it could change the "fully alien" direction.

---

## Amendment 4: Keyword Cost Verification

Current assumption: symbols are cheaper than keywords.
Challenge: common English keywords are often single tokens in code-trained BPE vocabularies.

If `fn` = 1 token and `@` = 1 token, there is zero token benefit to using `@` - and `fn` has lower ambiguity risk because it's familiar to the tokenizer's learned patterns.

**Test required:** For every abstract operator (FN_DEF, IF, ELSE, CASE, etc.), measure:
- The English keyword spelling (fn, if, else, case)
- 3-5 symbolic alternatives (@, ?, |, ->, etc.)
- In isolation AND in realistic context (preceded by whitespace, followed by typical constructs)

If keywords and symbols are equivalent in tokens, prefer keywords - they carry zero ambiguity risk and are merge-friendly.

**Action:** Use Prompt B from the research context:

```
Goal: find token-cheapest surface strings for a fixed set of abstract operators.
Operators to realize:
FN_DEF, IF, ELSE, CASE, ARROW, LET, LAMBDA, RESULT_OK, RESULT_ERR, PROPAGATE

Constraints:
- ASCII only
- Must be distinct and unambiguous
- Must not require whitespace to disambiguate

Propose 10 candidate surface strings per operator.
Return as JSON: { "FN_DEF": [...], "IF": [...], ... }
```

Then measure each candidate on the Qwen tokenizer in context.

---

## Amendment 5: Cross-Tokenizer Portability Baseline

Diamond's ingestion play targets all future LLMs, not just Qwen. Different tokenizers may produce different optimal encodings for the same syntax.

**Test required:** After locking the Qwen-optimal v0 syntax, measure the same programs on:
- Llama 3 tokenizer (tiktoken-based, 128K vocab)
- Llama 2 tokenizer (SentencePiece-based, 32K vocab)
- OpenAI o200k_base

If the Qwen-optimal syntax is also good (within 10% of optimal) on other tokenizers, the single syntax works. If there's significant divergence, the profile system from Amendment 1 becomes essential rather than nice-to-have.

**Action:** Add cross-tokenizer measurement to the pipeline after v0 syntax lock. Not blocking, but informative.

---

## Amendment 6: Stress Test Alien Wins on Complex Programs

Current data: C-style alien syntax wins at 56% average reduction across 5 programs.
Concern: these programs are relatively small and simple. Complex programs with deep nesting, many scopes, long identifier chains, and mixed data structures might show different results.

**Test required:** Run C candidates on the hardest programs in the corpus:
- 13_calculator (expression parser - recursive, nested)
- 18_trie (deep data structure)
- 19_config_parser (string-heavy, mixed constructs)
- 20_pubsub (concurrent patterns, callbacks)

If C still wins on these, the pattern genuinely generalizes. If it struggles, the language may need different strategies for different program shapes.

**Action:** Add to the next measurement batch.

---

## Priority Order

1. **Whitespace hypothesis test** (P0 - could change the entire direction)
2. **Keyword cost verification** (P0 - could change the alien vs familiar decision)
3. **Stress test on complex programs** (P1 - validates generalization)
4. **Compiler renamer prototype** (P1 - independent token savings)
5. **Cross-tokenizer portability** (P2 - not blocking v0)
6. **Profile system implementation** (P2 - becomes essential based on #5 results)

---

*These amendments are additive to docs/language/LANGUAGE_DESIGN.md. They don't replace the measurement-driven process - they add specific tests that need to run before any syntax decisions are frozen.*
