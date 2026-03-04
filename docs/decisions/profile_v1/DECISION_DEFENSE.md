# Diamond v1 Decision Defense

Purpose: document the core design decisions with measurable evidence, alternatives considered, and accepted tradeoffs.

Primary evidence sources:
- `research/benchmarks/measurements/decision_log.jsonl`
- `docs/reference/measurements/observations_q1.md`
- `docs/reference/measurements/amendments_p0_q1.md`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_validation.md`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`
- `docs/decisions/profile_v1/SYNTAX_PROFILE.md`
- `docs/decisions/profile_v1/AMBIGUITY_CHECKS.md`
- `docs/decisions/profile_v1/CONSTRUCT_TOOL_STYLE_GUIDE.md`
- `docs/decisions/profile_v1/VALIDATION.md`

---

## D1. Optimize for tokenizer tokens (not characters/readability)

Decision:
- Treat token count on target tokenizer as the objective function.

Alternatives considered:
- Character count minimization.
- Human readability prioritization.

Measured evidence:
- FizzBuzz: Python `159` vs candidate C `48` (`69.81%` reduction).
- HTTP routing spectrum: Python `115` vs alien inline `54` (`53.04%` reduction).
- Source: `docs/reference/measurements/observations_q1.md`.

Accepted tradeoff:
- Syntax can become non-human-friendly.
- Requires measurement pipeline for every significant syntax change.

Status:
- Locked principle.

---

## D2. Expression-dense control flow over block-heavy forms

Decision:
- Use expression-first forms (`?:`, match chains) as the default control-flow encoding.

Alternatives considered:
- Statement/block forms with explicit `if/else` blocks and delimiters.

Measured evidence:
- Isolated hypothesis (`branch_blocks_vs_inline`): `51 -> 32` (`37.25%` reduction).
- In 5-program A/B/C suite, C (expression-dense) wins all programs; total reduction `56.06%` vs Python.
- Source: `docs/reference/measurements/observations_q1.md`.

Accepted tradeoff:
- Increased precedence/associativity risk.
- Mitigated by grammar rules (right-assoc ternary, reserved operators) in ambiguity checks.

Status:
- Locked in profile v1 grammar and syntax profile.

---

## D3. Dense formatting is default for Qwen profile

Decision:
- Emit dense/minimal-whitespace Diamond by default for Qwen profile.

Alternatives considered:
- Formatted/indented style for readability or possible tokenizer merges.

Measured evidence:
- Whitespace P0 test: dense `341` vs formatted `529` (dense better by `188` tokens, `35.54%`).
- Source: `docs/reference/measurements/amendments_p0_q1.md`.

Accepted tradeoff:
- Harder manual debugging/inspection of raw source.
- Compensated by IR dumps and transpiled output for diagnostics.

Status:
- Locked for Qwen profile.

---

## D4. Symbol-heavy spellings are allowed, but uniqueness/disambiguation is mandatory

Decision:
- Do not assume words beat symbols or vice versa; measure both.
- Enforce globally distinct operator spellings per surface profile.

Alternatives considered:
- Always choose wordy keywords.
- Always choose symbols.

Measured evidence:
- Keyword-cost run shows many ties at 1-token candidates across both words and symbols.
- Raw minima collide across operators; uniqueness pass required (`mappings_unique`).
- Sources:
  - `research/benchmarks/measurements/keyword_cost_q1.csv`
  - `docs/reference/measurements/amendments_p0_q1.md`
  - `research/profiles/qwen3-8b.q1.surface.json`

Accepted tradeoff:
- Profile generation is more complex (global assignment, not per-operator local minima).
- Lower ambiguity risk than naive "pick local minimum everywhere."

Status:
- Locked process rule.

---

## D5. Tool layers are structural, but composition must share encoding

Decision:
- Keep tool behaviors (trace/capability/resource/error context) integrated with constructs.
- Compose layers via shared structure, not additive duplication.

Alternatives considered:
- Library-style external tooling only.
- Naive stacking of tool syntax.

Measured evidence:
- `fn_error` naive composition: tool overhead `25.63%` (fail).
- `fn_error_compose_v2`: tool overhead `13.57%` (pass) with similar net reduction.
- Sources:
  - `research/benchmarks/measurements/construct_tool_fn_error_q1.csv`
  - `research/benchmarks/measurements/construct_tool_fn_error_compose_q1_v2.csv`
  - `docs/reference/measurements/construct_tool_q1_summary.md`

Accepted tradeoff:
- Requires strict style constraints (header inheritance, sparse propagation points, no duplicated markers).

Status:
- Locked via style guide:
  - `docs/decisions/profile_v1/CONSTRUCT_TOOL_STYLE_GUIDE.md`

---

## D6. Gate model is portfolio-centric with per-program floors

Decision:
- Use final gates:
  - Portfolio `net_reduction >= 35%`
  - Portfolio `vs_python_with_tools >= 60%`
  - Portfolio `tool_overhead <= 15%`
  - Per-program `net_reduction >= 5%`
  - Per-program `tool_overhead <= 20%`

Alternatives considered:
- Earlier stricter universal gates (`40%` net portfolio, `15%` per-program overhead) across all shapes.

Measured evidence:
- Gate-lock run (`v4`):
  - Portfolio net reduction `40.23%`
  - vs_python_with_tools `65.29%`
  - tool_overhead `7.80%`
  - zero per-program gate failures.
- Source:
  - `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_validation.md`
  - `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`

Accepted tradeoff:
- Acknowledges shape-dependent compression instead of enforcing identical per-program compression behavior.

Status:
- Locked and validated.

---

## D7. Weak-shape uplift via targeted constructs, not wholesale syntax changes

Decision:
- Improve weak algorithmic/state-heavy shapes using localized proposals:
  - tool-header inheritance (P3),
  - inline single-use helpers (P4),
  - math constructs (`$`, `l()/r()`, `d0` usage where beneficial),
  - record patch on state-heavy programs.

Alternatives considered:
- Redesign core language structure.
- Keep weak-shape losses unaddressed.

Measured evidence:
- Portfolio `v2 -> v3.4` (P3+P4): net `34.12% -> 35.66%`.
- Math + patch (`v4_math_patch`): net `37.86%`, vs_python_with_tools `63.91%`.
- Final gate-lock outlier compression reaches net `40.23%`.
- Sources:
  - `docs/reference/measurements/construct_tool_portfolio14_v2_summary.md`
  - `docs/reference/measurements/construct_tool_portfolio14_v3_34_summary.md`
  - `docs/reference/measurements/math_constructs_weak_shapes_q1.md`
  - `docs/reference/measurements/construct_tool_portfolio14_v4_math_patch_summary.md`
  - `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_validation.md`

Accepted tradeoff:
- Extra construct complexity for specific shape families.
- Managed by parser ambiguity checks and explicit syntax constraints.

Status:
- Locked in `v4` validated scenario.

---

## D8. Parseability-first constraints on dense syntax

Decision:
- Preserve dense encoding but impose deterministic grammar constraints:
  - explicit named params in declarations,
  - reserved operator roles (`~`, `#`, etc.),
  - right-associative ternary,
  - contextual `:` disambiguation,
  - explicit postfix vs primary separation (`patch` vs map literal).

Alternatives considered:
- Fully unconstrained "shortest wins" syntax.

Measured evidence:
- Profile v1 parser validation passes `10/10` profile programs.
- Ambiguity checklist resolves each high-risk construct with explicit grammar rules.
- Sources:
  - `docs/decisions/profile_v1/VALIDATION.md`
  - `docs/decisions/profile_v1/AMBIGUITY_CHECKS.md`

Accepted tradeoff:
- Slight token cost in a few places to guarantee deterministic parse.
- `?[` is now reserved for postfix propagate+index/slice; ternary list-then-arms should use spacing or parentheses.

Status:
- Locked for profile v1 with explicit `?[` disambiguation rule.

---

## D9. Semantic IR with backend separation (no Python-shaped IR)

Decision:
- Keep IR language-agnostic and represent Diamond semantics directly.

Alternatives considered:
- Python-shaped IR shortcuts for faster initial transpiler.

Measured evidence:
- Shared parser/IR drives Python backend on full portfolio and keeps Rust/Wasm/JS emitters viable as independent backends.
- Sources:
  - `src/transpiler/README.md`
  - successful behavior/parity runs in this repo (`61/61` portfolio, Phase B `retry` `9/9`).

Accepted tradeoff:
- More upfront IR/runtime work.
- Better long-term backend portability and semantic consistency.

Status:
- Locked architecture for transpiler v0+.

---

## D10. Diamond-First Change Governance (ports as probes)

Decision:
- Treat real-project ports as structured discovery input for language evolution, not as the primary objective.
- Admit core language changes only through an explicit promotion gate.

Alternatives considered:
- Adapter-only growth without core promotion criteria.
- Port-first changes that bypass syntax/economics/ambiguity gates.

Measured/operational evidence:
- Recent difficult multi-file ports (`iniconfig`, `tomli`) surfaced concrete edge conditions while preserving gate-locked portfolio metrics.
- Differential case parity tooling exposed validation requirements (e.g., NaN-aware deep comparison, explicit non-UTF8 fixture policy) without requiring ad hoc language churn.
- Sources:
  - `certification/real-repos/REAL_REPO_CERTIFICATION_2026-03-03.md`
  - `docs/reference/certification/tomli/RESULTS.md`
  - `docs/reference/certification/tomli/FULL_PORT_GAP.md`
  - `docs/decisions/profile_v1/LANGUAGE_CHANGE_GATE.md`

Accepted tradeoff:
- Slightly slower feature admission in exchange for architectural coherence and reduced syntax drift.

Status:
- Locked governance rule for post-v1 core evolution.

---

## D11. Module System Layering (B-core default, C-contract extension)

Decision:
- Keep B-core inline blocks as the default grammar mode.
- Add C-contract as an orchestration extension for context-window pressure using generated contract comment lines (`//@...`), not new core grammar.

Alternatives considered:
- B-only forever (no context-pack mode).
- C as mandatory base grammar.

Measured evidence:
- B-core gates pass with low structural cost:
  - portfolio `structure_overhead=7.32%`, `tokens_per_edge=1.58`, parse-clean.
- C-contract keeps the same structural overhead on full source and provides context-pack shrink:
  - context packs reduce multiblock context by `33.57%` on the 3-program set.
  - both B and C rules payloads meet cold-start spec budget (`<=100` tokens).
- Sources:
  - `docs/reference/measurements/module_system_b_core_d10_q1.md`
  - `research/benchmarks/measurements/module_system_b_vs_c_d10_q1.md`
  - `docs/decisions/profile_v1/MODULE_SYSTEM_B_CORE.md`
  - `docs/decisions/profile_v1/MODULE_SYSTEM_C_CONTRACT.md`

Accepted tradeoff:
- C-context snapshots are orchestration-first records; contract-only dependencies compile to explicit runtime stubs.
- Full parity execution still requires complete block sources.

Status:
- Locked as layered policy: B-core default, C-contract optional extension.

---

## Current Defense Position (Public-Facing Summary)

What is proven:
- Token-efficient syntax decisions are measurement-backed, not aesthetic.
- Tool-layer composition can stay inside budget when encoded structurally.
- Final gate model is validated on full 14-program portfolio.
- Parsing is deterministic for profile v1 constructs with documented caveats.
- Real-project Phase B proof exists (`invl/retry` upstream tests pass against transpiled Diamond core).
- Language evolution is now controlled by an explicit Diamond-first promotion gate.

What remains explicit:
- Some syntax forms are still profile-specific optimizations (tokenizer-dependent).
- Parser ergonomics still require style discipline in dense ternary/list forms.
