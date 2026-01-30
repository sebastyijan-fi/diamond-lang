# Contributing to Diamond (<>)

Thank you for helping shape the Diamond programming language. This project aspires to set a new standard for agent-native languages, so we hold contributions to a high bar of clarity, security, and evidence-based design.

## Ground Rules

- **Be respectful and collaborate in good faith.** We follow the Rust Code of Conduct; report incidents to the core team.
- **Security first.** Never land code that relaxes capability boundaries or introduces ambient authority without a signed-off security review.
- **Evidence over intuition.** Back proposals with benchmarks, formal proofs, or user research whenever possible.

## Repository Structure Primer

- Language and runtime specs live in `docs/`.
- Implementation work happens under `packages/` (compiler, runtime, stdlib, LSP, tooling).
- Example agents and integration demos reside in `examples/`.
- Automation scripts belong in `scripts/`.
- Research artifacts and design explorations are in `research/` and `design/`.

## Guidance Documentation

Every directory in the Diamond repository includes a `GUIDANCE.md` file that provides localized contribution instructions. **Before contributing to any area, read the relevant guidance file.**

### Finding Guidance

| Area | Guidance Location | Covers |
| --- | --- | --- |
| Compiler | `packages/compiler/GUIDANCE.md` | Rust crates, testing, diagnostics |
| Runtime | `packages/runtime/GUIDANCE.md` | Effects, continuations, capabilities |
| Standard Library | `packages/stdlib/GUIDANCE.md` | Module design, API standards |
| Language Server | `packages/language-server/GUIDANCE.md` | LSP features, responsiveness |
| Tooling | `packages/tooling/GUIDANCE.md` | Transpiler, prompt packs |
| Examples | `examples/GUIDANCE.md` | Agent archetypes, integration patterns |
| Design Decisions | `docs/design-decisions/GUIDANCE.md` | RFCs, decision records |
| CI/Workflows | `.github/GUIDANCE.md` | Automation, governance checks |

### Guidance Hierarchy

Subdirectories inherit from parent guidance but may have specialized requirements:

```
packages/GUIDANCE.md                    # Workspace-wide standards
└── packages/compiler/GUIDANCE.md       # Compiler-specific standards
    └── packages/compiler/crates/GUIDANCE.md  # Crate organization
        └── packages/compiler/crates/frontend/GUIDANCE.md  # Parser/lexer specifics
```

When in doubt, start at the most specific guidance file and work up the hierarchy.

## How to Contribute

### 1. Discuss First (when in doubt)
- Check existing issues and design decision records in `docs/design-decisions/`.
- Open a GitHub issue for bugs or small enhancements.
- Use the RFC process (see below) for language/runtime changes, security model tweaks, or new standard-library modules.

### 2. Development Workflow
1. **Fork** the repository and create a feature branch (`feature/my-awesome-idea`).
2. **Sync** with `main` frequently to avoid merge drift.
3. **Write tests** alongside code changes (unit, integration, continuation-resume tests as relevant).
4. **Run the full validation suite**:
   - `scripts/dev/format.sh` for formatting/linting.
   - `scripts/dev/test.sh` for compiler/runtime/unit tests.
   - `scripts/dev/bench.sh` if performance is affected.
5. **Submit a pull request** to `main`, referencing related issues.

### 3. Pull Request Checklist
- ✅ Clear title and summary describing *why* the change is needed.
- ✅ Linked issue or RFC.
- ✅ Tests covering the change (or rationale for omissions).
- ✅ Updated documentation (spec, docs, examples, changelog entry).
- ✅ Security review (if capabilities, effects, or sandbox boundaries change).
- ✅ Performance/benchmarks where applicable.
- ✅ Screenshots or recordings for UX-facing tooling.

PRs that do not meet the checklist may be marked as draft or closed.

### 4. Code Style

- Source files use the `.dm` extension (alias `.dia` reserved).
- Follow the formatter output; do not fight automated formatting.
- Prefer semantic density over brevity—explicit effect usage, capability imports, and refined types are expected.
- Keep modules small and capability scope explicit (`import std/net requires { Network }`).
- Write descriptive comments for effect handlers, continuation serialization, and capability wrappers.

### 5. Commit Hygiene

- Use conventional-style messages (`feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`, `build:`, `chore:`).
- One logical change per commit; avoid large “kitchen sink” commits.
- Reference issues (`refs #123`) or close them when appropriate (`closes #123`).
- Rebase and squash as requested by reviewers to maintain a linear history.

## RFC Process

Large or sensitive changes require a Request for Comments:

1. Clone the RFC template (coming soon) into `docs/design-decisions/rfcs/`.
2. Fill in motivation, design, alternatives, security implications, backward compatibility, testing strategy.
3. Open a PR tagged `RFC`.
4. Engage in the discussion; consensus or core-team decision is required before merge.
5. Once accepted, implement the change and update the `docs/design-decisions/` index.

## Testing Expectations

- **Compiler:** front-end parsing snapshots, type checker conformance, HIR lowering, Wasm golden files.
- **Runtime:** effect handlers, continuation serialization/deserialization, capability enforcement, sandbox escape attempts.
- **Stdlib:** deterministic unit tests plus scenario-driven integration tests (agent workflows).
- **Tooling/LSP:** hover/completion fixtures and multi-client regression tests.
- **Performance:** compare against baseline metrics in `benchmarks/`; contributions must not regress critical paths without justification.

## Documentation

- Update `docs/spec/` for language semantics changes.
- Maintain `docs/architecture/` diagrams and sequence charts when altering runtime behavior.
- Extend `examples/` with runnable `.dm` code that showcases new capabilities.
- Keep README files in subdirectories accurate and concise.

## Release Engineering

- Changes affecting release notes should modify `CHANGELOG.md`.
- Version bumps are handled by release managers; coordinate before touching release manifests.
- Taggable milestones require green CI, updated docs, and signed release checklists.

## Governance

- The project is stewarded by working groups (Language, Runtime, Security, ML Enablement, Developer Experience).
- Core maintainers have final say on scope or direction when consensus cannot be reached, but decisions remain transparent and documented.
- We welcome new maintainers—consistent high-quality contributions and active participation in reviews is the path.

## Support Channels

- GitHub Discussions for questions and architecture conversations.
- Issue tracker for actionable bugs and feature requests.
- (Forthcoming) Community chat for synchronous collaboration; abide by the same Code of Conduct.

---

By contributing, you affirm that you have the right to license your work under the project’s open-source license and that you accept the contribution guidelines above. Diamond is a shared effort to make agentic systems safe, reliable, and brilliant—thank you for helping build it.