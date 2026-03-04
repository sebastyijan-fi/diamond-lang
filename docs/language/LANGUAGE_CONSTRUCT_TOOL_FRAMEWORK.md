# Diamond Construct-Tool Framework

**In Diamond, every syntax construct is also a tool. They are not separable.**

---

## The Principle

Other languages have syntax and tools as separate layers. You write code, then optionally add logging, testing, tracing, validation as libraries. Most code ships without them because the overhead isn't worth it.

Diamond fuses them. Each syntactic construct carries built-in behaviors that would be "tools" in other languages. You cannot write a Diamond function without it being traced. You cannot write a Diamond loop without it being resource-bounded. You cannot write a Diamond module without it declaring capabilities. These are not features you enable. They are what the constructs do.

The LLM generates one thing and gets multiple behaviors. The token cost of these behaviors is paid from the 60% savings the syntax already provides.

---

## Token Budget Model

```
Python baseline:                    1000 tokens (program with no tooling)
Diamond syntax reduction:           -600 tokens (60% compression)
Diamond built-in tool overhead:     +100 tokens (10% of original)
Diamond net:                         500 tokens

Result: 50% smaller than Python AND has logging, tracing,
        capability enforcement, resource limits, error context,
        and boundary validation that Python doesn't have.
```

The budget is spent per construct. Each construct's tool layer has a measured token cost.

---

## Construct Definitions

### 1. Function Definition

**Base semantic:** Declare a named computation with inputs and an output.

**Tool layer:**
- Capability declaration: what effects this function can perform
- Trace hook: entry and exit are logged with arguments and return value
- Resource budget: max execution steps / max memory (optional, default = inherited)
- Contract: input constraints and output guarantees

**What the LLM generates (single construct):**

```
[function-def] [name] [params+types] [capabilities] [body]
```

This one line of Diamond does what would take five separate mechanisms in Python:
```python
# Python equivalent of Diamond's single function construct:
import logging
import functools
import resource

logger = logging.getLogger(__name__)

CAPABILITIES = {"net.connect": ["api.example.com:443"]}

def handle(request: Request) -> Response:            # 1. definition
    logger.info(f"enter handle({request})")          # 2. trace
    assert isinstance(request, Request)              # 3. contract
    _step_counter = 0                                # 4. resource budget
    # ... body ...
    logger.info(f"exit handle -> {result}")           # 2. trace
    return result
```

### 2. Conditional / Branch

**Base semantic:** Choose a path based on a condition.

**Tool layer:**
- Branch trace: which branch was taken is recorded
- Exhaustiveness: all cases must be covered (no silent fallthrough)

**What the LLM generates:**

```
[case] [expression] [pattern->result] [pattern->result] ...
```

Every case expression in Diamond automatically records which arm matched. In Python, you'd add `logger.debug(f"took branch: {condition}")` manually - in Diamond, it's what branching does.

### 3. Loop / Iteration

**Base semantic:** Repeat a computation over a sequence or condition.

**Tool layer:**
- Resource counter: increments per iteration, halts if budget exceeded
- Iteration trace: count recorded in execution log
- Progress: optional yield of intermediate state for long-running loops

**What the LLM generates:**

```
[iter] [binding] [source] [body]
```

This cannot infinite-loop by default. The resource budget (inherited from the function or set explicitly) caps iterations. A Python `while True` with no break is a bug. In Diamond, it's a budget violation that halts cleanly.

### 4. Error Handling

**Base semantic:** Express that a computation can fail, and handle failure.

**Tool layer:**
- Context attachment: errors automatically carry the call site and active state
- Trace recording: every error is logged with full context
- Propagation tracking: the error trace shows the full propagation chain

**What the LLM generates:**

```
[fallible-call]?
```

The `?` propagation operator doesn't just pass the error up - it attaches context at each level it passes through. By the time an error reaches the top, it carries a complete breadcrumb trail. In Rust, you add `.context("doing X")?` at every call site. In Diamond, context is what propagation does.

### 5. Module Declaration

**Base semantic:** Group related computations and declare their shared context.

**Tool layer:**
- Capability manifest: complete list of effects this module can perform
- Dependency declaration: what other modules are required
- Visibility control: what is exported vs internal
- Version tag: spec version this module was generated against

**What the LLM generates:**

```
[module] [name] [capabilities] [dependencies] [body]
```

A Diamond module is also its own security policy. No separate config file. No separate permissions manifest. The module declaration IS the manifest.

### 6. Binding (Variable Declaration)

**Base semantic:** Associate a name with a value.

**Tool layer:**
- Immutability by default (mutable requires explicit marking)
- Type constraint (inferred or declared)
- Scope tracking in trace

**What the LLM generates:**

```
[bind] [name] [expression]
```

Immutable unless explicitly marked otherwise. The trace records every binding for replay.

### 7. External Boundary (I/O, Network, File)

**Base semantic:** Interact with something outside the program.

**Tool layer:**
- Capability check: is this effect permitted by the module's declaration?
- Input validation: data entering the program is validated against type constraints
- Output sanitization: data leaving the program is checked against declared formats
- Trace recording: every boundary crossing is logged with timestamp

**What the LLM generates:**

```
[perform] [effect] [arguments]
```

Every boundary crossing is validated, logged, and capability-checked. In other languages, you'd wrap every I/O call in try/catch with logging and validation. In Diamond, I/O does that automatically.

---

## Design Process Per Construct

For each of the ~40 language constructs:

```
1. Define base semantic
   What does this construct compute?

2. Identify tool layer
   What behaviors should ride along for free?
   - Tracing?
   - Validation?
   - Resource limiting?
   - Capability checking?
   - Error context?

3. Design unified syntax
   One construct that expresses both the computation
   and the tool behaviors. Not two things composed -
   one thing that IS both.

4. Measure token cost
   a. Base semantic alone (minimal Diamond)
   b. Base + tool layer (full Diamond)
   c. Python equivalent with same tool behaviors added manually

   The construct is valid if:
   (b) < Python baseline without tools
   AND (b) is within token budget allocation

5. Ambiguity check
   Does the tool layer create parsing ambiguity?
   Does it interact badly with other constructs' tool layers?

6. Lock and log
   Record the decision, measurements, and rationale.
```

---

## Budget Allocation Per Construct

Target: total tool overhead stays under 15% of the syntax-reduced program size.

| Construct | Estimated frequency | Tool layer | Budget per occurrence |
|-----------|-------------------|------------|---------------------|
| Function def | Medium (5-20 per program) | Trace + capabilities + contract | 3-5 tokens |
| Conditional | High (10-50 per program) | Branch trace + exhaustiveness | 0-1 tokens |
| Loop | Medium (5-15 per program) | Resource counter + trace | 1-2 tokens |
| Error propagation | Medium (5-20 per program) | Context attachment | 0-1 tokens |
| Module declaration | Low (1-5 per program) | Capability manifest | 5-10 tokens |
| Binding | High (20-100 per program) | Immutability + scope trace | 0 tokens (default behavior) |
| External boundary | Low-Medium (1-10 per program) | Validation + capability check | 2-4 tokens |

Most tool behaviors add 0-2 tokens per occurrence because they're implicit in the construct syntax, not additional syntax bolted on.

---

## What This Means For The Flywheel

When the LLM converts a Python project to Diamond:

1. The Python code has no logging -> Diamond version has full execution tracing
2. The Python code has no capability declarations -> Diamond version has explicit capability manifest
3. The Python code has no resource limits -> Diamond version has bounded loops and recursion
4. The Python code has scattered error handling -> Diamond version has context-rich error propagation
5. The Python code has tests in separate files -> Diamond version has contracts embedded in the code

The converted project is not just "the same code in a shorter language." It is the same logic with more safety guarantees, in fewer tokens, with no human effort to add the safety layer.

This is the value proposition that goes beyond token efficiency: Diamond programs are simultaneously smaller AND more trustworthy than their source language equivalents.

---

## Measurement Integration

Add to tokenbench:

```
For each benchmark program, measure:
  - python_tokens:          baseline Python, no tools
  - python_with_tools:      Python with logging + typing + validation added
  - diamond_base:           Diamond syntax only, no tool layer
  - diamond_full:           Diamond with tool layer

Report:
  - syntax_reduction:       (python - diamond_base) / python
  - tool_overhead:          (diamond_full - diamond_base) / diamond_base
  - net_reduction:          (python - diamond_full) / python
  - vs_python_with_tools:   (python_with_tools - diamond_full) / python_with_tools
```

The last metric is the real killer: how does Diamond-with-everything compare to Python-with-the-same-capabilities-added-manually? That number should be 70%+ reduction because Python's tool overhead is massive (imports, decorators, try/catch blocks, logging calls, assert statements).

---

*This framework is additive to docs/language/LANGUAGE_DESIGN.md and docs/language/LANGUAGE_DESIGN_AMENDMENTS.md. Each construct gets designed with its tool layer simultaneously, not bolted on after.*
