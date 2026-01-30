# Tooling Package Guidance

## Purpose
The `packages/tooling/` workspace houses developer tools, utilities, and machine-learning enablement components that support the Diamond ecosystem. These tools bridge the gap between language development and practical adoption, enabling synthetic corpus generation, IDE integration, and LLM-assisted development workflows. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Synthetic bootstrapping strategy, transpiler architecture, and ML enablement pipelines.
- **`diamond3.md`** — Grammar specification, semantic typing, and module-level capability injection.

The tooling package accelerates Diamond's adoption by providing the infrastructure for bootstrapping, development, and AI-assisted coding.

---

## Directory Contract

| Path | Owner Working Groups | Scope & Expectations |
| --- | --- | --- |
| `transpiler/` | ML Enablement + Language | Python→Diamond transpiler for synthetic corpus generation. |
| `prompt-packs/` | ML Enablement + DX | Curated prompt templates for LLM-assisted Diamond development. |
| `fmt/` (planned) | Developer Experience | Diamond source code formatter. |
| `docgen/` (planned) | Developer Experience | Documentation generator from Diamond source. |
| `repl/` (planned) | Developer Experience | Interactive Diamond REPL for exploration. |
| `README.md` | All WGs | Overview of available tools, installation, and usage. |
| `GUIDANCE.md` | All WGs | This file—contribution and quality standards. |

Subdirectories must not be created without an owning working group, README, and guidance note.

---

## Tooling Philosophy

1. **Capability Respect**: All tools must operate within Diamond's capability model—no ambient authority.
2. **Determinism**: Tools should produce deterministic output for reproducibility.
3. **Composability**: Tools should integrate with Unix pipelines and CI workflows.
4. **Documentation**: Every tool must be self-documenting via `--help` and README.
5. **Telemetry**: Tools should optionally emit metrics for quality tracking.

---

## Subdirectory Expectations

### `transpiler/`
The transpiler converts Python code to Diamond, supporting the synthetic bootstrapping strategy.

**Responsibilities:**
- Parse Python source code (subset supported).
- Generate equivalent Diamond `.dm` code.
- Preserve semantic intent where possible.
- Document limitations and unsupported patterns.
- Integrate with synthetic corpus pipeline.

**Quality Criteria:**
- Parse rate > 90% for idiomatic Python.
- Generated Diamond should type-check (once compiler available).
- Round-trip testing where applicable.
- Clear error messages for unsupported constructs.

### `prompt-packs/`
Curated prompt templates for LLM-assisted Diamond development.

**Responsibilities:**
- Provide task-specific prompts (code generation, review, debugging).
- Include metadata (model targets, capability requirements, safety constraints).
- Version and test prompts against model outputs.
- Document expected behaviors and limitations.

**Quality Criteria:**
- Prompts tested against target LLM models.
- Safety constraints documented and tested.
- Capability requirements specified in metadata.
- Examples included for each prompt type.

### `fmt/` (Planned)
Source code formatter for Diamond.

**Responsibilities:**
- Format `.dm` files according to style guide.
- Support check mode (`--check`) for CI.
- Integrate with editor save-on-format.
- Preserve semantic meaning exactly.

### `docgen/` (Planned)
Documentation generator from Diamond source.

**Responsibilities:**
- Extract doc comments from `.dm` files.
- Generate Markdown or HTML documentation.
- Support cross-referencing and search.
- Include capability and effect documentation.

### `repl/` (Planned)
Interactive REPL for Diamond exploration.

**Responsibilities:**
- Parse and evaluate Diamond expressions.
- Provide completion and inline help.
- Support effect simulation for testing.
- Sandbox execution with configurable capabilities.

---

## Development Standards

### Code Organization
```
<tool-name>/
├── Cargo.toml          # Rust tools
├── pyproject.toml      # Python tools
├── README.md           # Tool documentation
├── GUIDANCE.md         # Local guidance (or defer to parent)
├── src/                # Source code
├── tests/              # Test suites
├── examples/           # Usage examples
└── docs/               # Additional documentation
```

### CLI Conventions
- Use `clap` for Rust CLIs, `click` or `argparse` for Python.
- Provide `--help` with examples.
- Support `--version` flag.
- Use exit codes: 0 (success), 1 (error), 2 (usage error).
- Support `--quiet` and `--verbose` modes.
- Output to stdout, errors to stderr.

### Testing Requirements
- Unit tests for core logic.
- Integration tests with sample inputs.
- Golden tests for output stability.
- Performance benchmarks for heavy operations.

### Documentation
- README with installation, usage, and examples.
- `--help` output that serves as quick reference.
- Changelog tracking user-visible changes.
- Spec references for language-related behavior.

---

## Synthetic Corpus Pipeline

The tooling package supports Diamond's bootstrap strategy:

```
Python Codebase                    Synthetic Corpus
      │                                  ▲
      ▼                                  │
┌─────────────┐                   ┌──────┴───────┐
│ Transpiler  │                   │  Validation  │
│ (Python→DM) │                   │  (Compiler)  │
└──────┬──────┘                   └──────────────┘
       │                                  ▲
       ▼                                  │
┌─────────────┐                   ┌───────┴──────┐
│  LLM        │──────────────────►│  Generated   │
│  Evolution  │                   │  .dm Files   │
└─────────────┘                   └──────────────┘
```

### Pipeline Integration Points
- `scripts/bootstrap_corpus.py` orchestrates the pipeline.
- Transpiler outputs feed into LLM evolution loops.
- Compiler validates generated Diamond code.
- Metrics track parse rate, type-check rate, and quality.

---

## Prompt Pack Standards

### Metadata Format
```yaml
# prompt_metadata.yaml
name: "code-generation-basic"
version: "1.0.0"
description: "Generate Diamond code from natural language descriptions"
models:
  - "gpt-4"
  - "claude-3-opus"
  - "diamond-llama"  # future
capabilities:
  - "code_generation"
safety_constraints:
  - "no_capability_escalation"
  - "no_ambient_authority"
author: "Diamond Team"
last_updated: "2025-01-15"
```

### Prompt Structure
```
prompts/
├── code-generation/
│   ├── prompt_metadata.yaml
│   ├── system.txt
│   ├── user_template.txt
│   ├── examples/
│   │   ├── example1_input.txt
│   │   ├── example1_output.dm
│   │   └── ...
│   └── tests/
│       ├── test_cases.yaml
│       └── expected_outputs/
└── code-review/
    └── ...
```

### Testing Prompts
- Define test cases with expected output patterns.
- Run against target models periodically.
- Track quality metrics over time.
- Flag regressions in prompt effectiveness.

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the tool or enhancement.
   - Identify target users and use cases.
   - Reference relevant spec sections.
   - Propose integration with existing tooling.

2. **Implementation**
   - Follow the tool structure template.
   - Implement core functionality with tests.
   - Add documentation and examples.
   - Integrate with CI for validation.

3. **Review**
   - Ensure CLI follows conventions.
   - Validate capability respect.
   - Check documentation completeness.
   - Verify deterministic output.

4. **Release**
   - Update changelog.
   - Tag version appropriately.
   - Announce to relevant channels.

---

## Quality Checklist (Pre-Merge)

- [ ] Tool has comprehensive `--help` output.
- [ ] README documents installation, usage, and examples.
- [ ] Unit and integration tests pass.
- [ ] Output is deterministic for given inputs.
- [ ] Capability model is respected (no ambient authority).
- [ ] Error messages are clear and actionable.
- [ ] Performance is acceptable for typical use cases.
- [ ] CI integration is documented.
- [ ] Changelog updated for user-visible changes.
- [ ] Spec references included where applicable.

---

## CI Integration

Tools should integrate with repository CI:

```yaml
# Example CI job for tooling
tooling-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Setup Rust
      uses: dtolnay/rust-action@stable
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Run transpiler tests
      run: cargo test -p diamond-transpiler
    - name: Validate prompt packs
      run: python scripts/validate_prompts.py
```

---

## Future Enhancements

- Unified CLI (`diamond-tools`) wrapping all utilities.
- Plugin architecture for third-party tool extensions.
- Web-based playground using tooling infrastructure.
- IDE extensions leveraging tooling APIs.
- Telemetry dashboard for corpus quality metrics.
- Integration with package registry (Gem) for distribution.

---

The tooling package is Diamond's force multiplier—enabling bootstrapping, development, and AI-assisted workflows. Build tools that developers love to use, that respect Diamond's principles, and that accelerate the ecosystem's growth.