# Diamond Language Design

**Working document. This is what you open when you sit down with the local Qwen.**

Diamond is a programming language optimized for LLM token efficiency. No human reads it, writes it, or debugs it. The syntax should be as alien as necessary to minimize token count while remaining unambiguous and parseable.

This document frames the design problem, shows the compression spectrum, and defines the process for finding the real syntax.

Latest addenda:
- `docs/language/LANGUAGE_DESIGN_AMENDMENTS.md` (tokenizer-profile system, renamer pass, and required measurement tests)
- `docs/language/LANGUAGE_CONSTRUCT_TOOL_FRAMEWORK.md` (construct-level tool fusion and four-way token budget model)

---

## The Optimization Target

Diamond's syntax is optimized against a specific measurable quantity: **tokens as counted by the target LLM's tokenizer.**

Not characters. Not lines. Not "readability." Tokens — the actual units the model consumes and produces. A design choice is better if it reduces token count for the same semantic content.

This means the design process is empirical, not aesthetic. Every choice gets measured. If `@` costs 1 token and `fn` costs 1 token, they're equivalent. If `->` costs 1 token but `→` costs 2, use `->`. The tokenizer is the judge.

Key insight: LLM tokenizers (BPE-based) don't see characters — they see learned byte-pair chunks. Common English words like `function` or `return` are often single tokens because they appear constantly in training data. Symbols like `@` or `#` are also usually single tokens. But *uncommon combinations* of symbols might cost more tokens than a short English word. **You cannot assume shorter = fewer tokens.** You must measure.

---

## The Compression Spectrum

Here's the same program — an HTTP handler that routes GET requests and returns JSON — at four compression levels. This shows what "fully alien" actually means in practice.

### Level 0: Python (baseline)

```python
from http import Request, Response, json_response

def handle(request: Request) -> Response:
    if request.method == "GET":
        if request.path == "/users":
            users = get_all_users()
            return json_response(200, users)
        elif request.path == "/health":
            return json_response(200, {"status": "ok"})
        else:
            return json_response(404, {"error": "not found"})
    else:
        return json_response(405, {"error": "method not allowed"})
```

### Level 1: Terse human (the v0 candidate we scrapped)

```
fn handle(req:Request)->Response{
  if req.method=="GET"{
    match req.path{
      "/users"->json(200,get_all_users())
      "/health"->json(200,{status:"ok"})
      _->json(404,{error:"not found"})
    }
  }else{json(405,{error:"method not allowed"})}
}
```

### Level 2: Symbolic but structured

```
@handle(r:Req)->Res{
  ?r.m=="GET"{
    |r.p|"/users"->J(200,users())"/health"->J(200,{s:"ok"})_->J(404,{e:"nf"})|
  }!{J(405,{e:"mna"})}
}
```

### Level 3: Fully alien (one possible direction)

```
h:Req>Res=r.m~G?r.p~"/users":J200(U)~"/health":J200{s:ok}~_:J404{e:nf}|J405{e:mna}
```

### What changes across levels

| Aspect | Level 0 | Level 1 | Level 2 | Level 3 |
|--------|---------|---------|---------|---------|
| Human readable | Yes | Mostly | Barely | No |
| Keywords | English words | Short English | Symbols | Eliminated |
| Structure | Indented blocks | Braces | Braces + density | Inline expressions |
| Names | Full words | Abbreviated | Single chars | Single chars |
| Punctuation purpose | Grouping | Grouping | Semantics | Semantics |
| Whitespace | Significant | Formatting | Minimal | None/minimal |

**The question is: which level actually produces the fewest tokens?** Level 3 looks smaller in characters but might tokenize *worse* than Level 1 because the tokenizer has never seen those patterns and has to break them into individual bytes.

**This is why we measure, not guess.**

---

## What Needs To Be Decided

These are the core design questions. Each one should be resolved by generating alternatives and measuring token cost across a benchmark corpus.

### 1. What is the basic unit of a program?

Traditional languages have statements and expressions. Some languages are expression-only (everything returns a value). Some use declarations as the top-level unit.

Options to test:
- **Statement-based** (like Python/Go): sequence of instructions
- **Expression-based** (like Haskell/Lisp): everything is an expression that returns a value
- **Pattern-match-based**: program is a set of pattern → result rules
- **Something else**: let the LLM propose

The question for the local Qwen: "Given that token efficiency is the only goal, what should the fundamental unit of computation be? Generate three candidate models, express the same 10 programs in each, measure tokens."

### 2. How is control flow expressed?

Options:
- Traditional: `if`/`else`, `for`, `while`, `match`
- Pattern matching only: all branching is pattern matching, loops are recursion or map/filter
- Symbolic operators: `?` for branch, `*` for iterate, `|` for match
- Inline conditionals: everything is ternary-style, no block structure
- Something else

Key question: do block-structured control flow constructs (which require open/close delimiters) cost more tokens than inline expression-based alternatives? Measure it.

### 3. How are functions defined and called?

Options:
- Named declarations: `fn name(args) -> type { body }` (various compressions)
- Lambda-only: all functions are anonymous, bound to names via `let`
- Implicit: functions are defined by their pattern signature, no keyword needed
- Concatenative: stack-based, no named arguments (like Forth)

### 4. How are types expressed?

Options:
- Fully explicit everywhere
- Fully inferred everywhere (like Haskell with no signatures)
- Explicit at boundaries, inferred internally (like Rust)
- Structural only (duck typing, no type names)
- Single-character type abbreviations (`i`, `s`, `f`, `b`)
- Encoded in the name itself (Hungarian-style but for machines)

### 5. What is the naming convention?

Humans use descriptive names because they need to remember what things mean. LLMs don't — they have the full context window. Options:
- **Full names**: `request`, `response`, `user_list` (human legacy)
- **Abbreviated**: `req`, `res`, `usr` (compromise)
- **Positional**: no names, everything referenced by position or pattern
- **Hash-based**: auto-generated unique identifiers
- **Single char + scope**: `r` for request in this scope, `s` for string in this scope

### 6. What does the module/import system look like?

Options:
- File-based modules with import statements
- Everything in one stream, namespaced by prefix
- No import — all capabilities declared inline
- Content-addressed: modules referenced by hash of their content

### 7. What is the error model?

Options:
- Result types (`Ok`/`Err`) with propagation operator
- Algebraic effects
- Exceptions
- Error codes (C-style)
- Condition system (Lisp-style)
- No error model in v0 — programs that fail just fail

### 8. How is data structured?

Options:
- Records/structs with named fields
- Tuples only (positional)
- Maps/dictionaries as the universal structure
- Algebraic data types
- All of the above with different syntax weights

---

## The Design Process

This runs on the local Qwen. It's a loop.

### Step 1: Build the benchmark corpus

Pick 20 small, well-defined programs that together cover the full range of programming constructs:

- Arithmetic and string manipulation
- Branching (if/else, match/switch)
- Loops (iteration, accumulation, transformation)
- Function definition and calls
- Error handling
- Data structures (lists, maps, records)
- Recursion
- Higher-order functions
- I/O (file read, network request)
- Concurrency (if applicable)

Express each in Python. These are the reference implementations. Count tokens for each using the Qwen tokenizer. This is the baseline to beat.

Suggested programs:
1. FizzBuzz
2. Fibonacci (recursive + iterative)
3. JSON parser (simplified)
4. URL router
5. Rate limiter (token bucket)
6. HTTP handler with routing
7. Key-value store (in-memory)
8. CSV parser
9. Binary search
10. Merge sort
11. Stack implementation
12. Queue implementation
13. Simple calculator (expression parser)
14. String template engine
15. Event emitter
16. Retry with exponential backoff
17. LRU cache
18. Trie (prefix tree)
19. Config file parser (INI or TOML subset)
20. Pub/sub message broker (in-memory)

### Step 2: Explore syntax candidates

For each design question above, have the local Qwen generate 3-5 alternative approaches. Express the benchmark corpus in each candidate syntax. Measure token counts.

The prompt pattern for the local Qwen:

```
You are designing a programming language called Diamond.
The sole optimization target is minimal token count on your own tokenizer.
Human readability is explicitly not a goal.
The language must be unambiguous and parseable.

Here is a program expressed in Python:
[python code]

Propose three alternative syntaxes that encode the same semantics.
For each, explain why it might minimize tokens.
Then I will measure which one actually does.
```

### Step 3: Converge

After measuring across the full benchmark corpus:
- Pick the winning approach for each design question
- Combine them into a unified syntax
- Re-measure the full corpus in the unified syntax
- Compare to Python baseline
- If token reduction is below 40%, iterate further
- If above 40%, lock the syntax and move to formalization

### Step 4: Formalize

Write the grammar (EBNF). Build a parser (Lark or tree-sitter). Build the transpiler (Diamond → Python). Run the benchmark corpus through the full pipeline: Python reference → hand-convert to Diamond → transpile back to Python → run original test → verify equivalence.

---

## Measurement Protocol

Every design decision follows this protocol:

```
1. State the question (e.g., "how should loops be expressed?")
2. Generate N candidates
3. Express 5+ benchmark programs in each candidate
4. Tokenize each with the Qwen tokenizer
5. Record: total tokens, tokens per construct, ambiguity risk
6. Pick the winner
7. Document the decision and the measurements
```

### Token counting setup

```bash
# Using Ollama + Python
pip install tiktoken transformers

# Or count directly via the model's tokenizer:
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
count = len(tok.encode(diamond_source))
```

### What to record for each measurement

```
program:          fizzbuzz
candidate:        A (symbolic control flow)
diamond_tokens:   47
python_tokens:    89
reduction:        47.2%
ambiguity_notes:  none — parse is deterministic
```

Build this into a spreadsheet or JSON log from day one. Every design decision needs a paper trail of measurements. No vibes. No "this feels cleaner." Numbers only.

---

## Open Questions That Only Measurement Can Answer

These are hypotheses. The local Qwen + tokenizer will confirm or destroy them.

1. **"Shorter source = fewer tokens" — probably false.** BPE tokenizers learn common patterns. `return` is probably 1 token. `>` is probably 1 token. They might be equivalent. But `>>>` might be 1 token or 3 depending on training data.

2. **"Symbols are cheaper than words" — test it.** `fn` vs `@` vs `λ` — which actually costs fewer tokens? Unicode symbols might cost more because they're less common in training data.

3. **"Eliminating whitespace saves tokens" — test it.** Some tokenizers treat whitespace as separate tokens. Others merge `\n  ` into a single indent token. The optimal whitespace strategy depends on the specific tokenizer.

4. **"Expression-based is cheaper than statement-based" — test it.** Expressions might save tokens by eliminating `return` keywords, but might cost tokens through deeper nesting.

5. **"Single-character names save tokens" — probably true but test the edge cases.** `r` is 1 token. `request` is 1 token. But `r.m` vs `request.method` — the dot access might interact differently with the tokenizer.

6. **"No keywords at all is optimal" — probably false.** Pure symbolic syntax might force the tokenizer to process character-by-character, which could cost MORE tokens than short English keywords that exist in its vocabulary.

7. **"The optimal syntax looks like nothing we've seen" — maybe.** Or maybe it looks like a compressed Lisp. Or maybe it looks like APL. The only way to know is to let the LLM propose and then measure.

---

## Success Criteria

Diamond v0 syntax is done when:

- [ ] All 20 benchmark programs are expressed in Diamond
- [ ] Average token reduction vs Python is ≥40%
- [ ] No ambiguity — every Diamond program has exactly one parse
- [ ] A formal grammar exists (EBNF)
- [ ] A parser exists and can parse all 20 programs
- [ ] A transpiler exists (Diamond → Python) and all programs round-trip correctly
- [ ] Every design decision has a measurement log entry
- [ ] The syntax document is frozen — this is v0, it doesn't change

---

## What This Document Is Not

This is not the Diamond README. This is not marketing. This is not a spec. This is the working document for the first real design session: sit down with the local Qwen, start with FizzBuzz and the HTTP handler, and find out what a token-optimized programming language actually looks like.

The README gets written after we know what Diamond is. Not before.

---

*Diamond is created by Sebastyijan.*
