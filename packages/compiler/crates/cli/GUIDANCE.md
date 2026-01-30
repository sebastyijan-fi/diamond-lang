# CLI Crate Guidance

## Purpose
The `packages/compiler/crates/cli/` crate provides the `diamondc` command-line interface—the primary user-facing entry point for the Diamond compiler toolchain. This crate orchestrates the compilation pipeline and delivers a polished developer experience. All functionality must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented language design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and zero-trust WebAssembly runtime.
- **`diamond3.md`** — Grammar specification, semantic typing, algebraic effects, and module-level capability injection rules.

---

## Directory Contract

| Path | Purpose |
| --- | --- |
| `src/lib.rs` | Core CLI logic, command parsing, pipeline orchestration. |
| `src/main.rs` | Binary entry point delegating to library. |
| `src/commands/` | Subcommand implementations (build, check, emit, fmt). |
| `src/output/` | Diagnostic formatting, terminal rendering, JSON output. |
| `src/config/` | Configuration file parsing, environment variable handling. |
| `tests/` | Integration tests for CLI behavior. |
| `README.md` | User documentation, usage examples, option reference. |
| `GUIDANCE.md` | This file—contribution standards for CLI development. |

---

## Command Structure

### Primary Commands

```
diamondc <COMMAND> [OPTIONS] [FILES...]

Commands:
  build       Compile Diamond source files to Wasm components
  check       Type-check source files without emitting output
  emit        Output intermediate representations (ast, hir, wasm-text)
  fmt         Format Diamond source files
  version     Display version information
  help        Display help for commands
```

### Global Options

| Option | Description |
| --- | --- |
| `--color <when>` | Color output: auto, always, never |
| `--quiet` | Suppress non-error output |
| `--verbose` | Enable verbose logging |
| `--json` | Emit diagnostics as JSON for tooling integration |
| `--config <file>` | Path to configuration file |

### Build Command Options

| Option | Description |
| --- | --- |
| `--output <path>` | Output file or directory |
| `--emit <type>` | Emit intermediate: ast, hir, wasm, wasm-text |
| `--target <spec>` | Target specification (default: wasm32-component) |
| `--capability-manifest` | Generate capability manifest alongside output |
| `--optimize <level>` | Optimization level: 0, 1, 2, 3, s, z |
| `--debug-info` | Include debug information in output |

### Check Command Options

| Option | Description |
| --- | --- |
| `--all-targets` | Check all modules in the project |
| `--deny <lint>` | Treat specific warnings as errors |
| `--explain <code>` | Explain a diagnostic code |

---

## Diagnostic Formatting

The CLI produces diagnostics that are:

1. **Human-Readable**: Clear messages with source context and suggestions.
2. **Machine-Parseable**: JSON mode for IDE/tooling integration.
3. **Accessible**: Support for color-blind-friendly palettes and screen readers.

### Terminal Output Example
```
error[E2001]: type mismatch
  --> src/agent.dm:15:10
   |
15 |     let result: Int = fetch_data()
   |                       ^^^^^^^^^^^^
   |                       |
   |                       expected `Int`, found `String`
   |
   = note: `fetch_data` returns `String` as defined at src/api.dm:8
   = help: consider using `parse_int(fetch_data())`
```

### JSON Output Schema
```json
{
  "diagnostics": [
    {
      "code": "E2001",
      "severity": "error",
      "message": "type mismatch",
      "span": {
        "file": "src/agent.dm",
        "start": { "line": 15, "column": 10 },
        "end": { "line": 15, "column": 22 }
      },
      "labels": [...],
      "notes": [...],
      "suggestions": [...]
    }
  ],
  "summary": { "errors": 1, "warnings": 0 }
}
```

---

## Implementation Standards

1. **Argument Parsing**
   - Use `clap` with derive macros for type-safe argument handling.
   - Provide shell completion generation (`--generate-completions`).
   - Support both short (`-o`) and long (`--output`) option forms.
   - Validate arguments early; fail fast with clear messages.

2. **Error Handling**
   - Use `anyhow` for application errors with context chaining.
   - Use `miette` for rich diagnostic rendering.
   - Exit codes: 0 (success), 1 (compilation errors), 2 (usage errors).
   - Never panic; convert all errors to user-friendly messages.

3. **Output Control**
   - Respect `--quiet`, `--verbose`, and `--color` flags throughout.
   - Use stderr for diagnostics, stdout for requested output.
   - Support `--json` for machine-parseable diagnostics.
   - Provide progress indicators for long-running operations.

4. **Configuration**
   - Support `diamond.toml` project configuration files.
   - Allow environment variable overrides (`DIAMOND_*`).
   - Merge CLI flags > environment > config file > defaults.
   - Document all configuration options in `README.md`.

5. **Testing**
   - Use `assert_cmd` and `predicates` for CLI behavior tests.
   - Test all exit codes and error message formats.
   - Snapshot test diagnostic output for consistency.
   - Test configuration file parsing and merging.

---

## Code Organization

```rust
// src/lib.rs - Main orchestration
pub mod commands;
pub mod config;
pub mod output;

pub fn run(args: Args) -> Result<ExitCode> {
    // Initialize logging
    // Load configuration
    // Dispatch to command handler
    // Format and emit diagnostics
    // Return exit code
}
```

```rust
// src/commands/build.rs
pub fn execute(opts: BuildOpts, config: &Config) -> Result<BuildOutput> {
    let sources = collect_sources(&opts)?;
    let asts = frontend::parse_all(&sources)?;
    let hirs = hir::lower_and_check(&asts)?;
    let wasm = backend::emit(&hirs, &opts.target)?;
    write_output(&wasm, &opts.output)?;
    Ok(BuildOutput { diagnostics, artifacts })
}
```

---

## Development Workflow

1. **Building**
   ```bash
   cargo build -p diamond-cli
   # Binary at target/debug/diamondc
   ```

2. **Testing**
   ```bash
   cargo test -p diamond-cli
   # Integration tests with sample files
   cargo test -p diamond-cli --test cli_integration
   ```

3. **Running**
   ```bash
   cargo run -p diamond-cli -- build examples/hello.dm --emit wasm-text
   cargo run -p diamond-cli -- check --all-targets
   cargo run -p diamond-cli -- --help
   ```

4. **Generating Completions**
   ```bash
   diamondc --generate-completions bash > completions.bash
   diamondc --generate-completions zsh > _diamondc
   ```

---

## Dependency Guidelines

| Dependency | Purpose | Rationale |
| --- | --- | --- |
| `clap` | Argument parsing | Industry standard, derive macros, completions |
| `anyhow` | Application errors | Ergonomic context chaining |
| `miette` | Rich diagnostics | Terminal formatting, source snippets |
| `serde` | Config parsing | TOML/JSON configuration files |
| `tracing` | Logging/diagnostics | Structured logging, spans |
| `indicatif` | Progress bars | User feedback for long operations |

Minimize dependencies; prefer well-maintained, security-audited crates.

---

## Quality Checklist (Pre-Merge)

- [ ] All commands have `--help` text with examples.
- [ ] Exit codes follow convention (0/1/2).
- [ ] Diagnostics render correctly in terminal and JSON modes.
- [ ] Configuration merging (CLI > env > file > default) tested.
- [ ] Shell completions generate correctly for bash/zsh/fish.
- [ ] Error messages are actionable and user-friendly.
- [ ] Performance is acceptable for typical project sizes.
- [ ] No panics; all errors converted to results.
- [ ] README documents all options and configuration.
- [ ] Integration tests cover primary use cases.

---

## Future Enhancements

- Watch mode with incremental recompilation (`--watch`).
- Language server integration (`diamondc lsp`).
- Project scaffolding (`diamondc new <name>`).
- Package management integration (`diamondc add <dep>`).
- Profile-guided optimization hints.
- Remote compilation for CI/CD integration.
- WASI preview 2 target support.

---

The CLI is often the first interaction developers have with Diamond. Invest in clear error messages, responsive feedback, and intuitive defaults to make that first experience excellent.