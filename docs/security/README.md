# Diamond Security Portal

This directory consolidates the policies, threat models, and operational guidance that ensure Diamond (<>) maintains a zero-trust posture from source code to runtime deployment. Security is a first-class design constraint for the language, compiler, runtime, and ecosystem tooling; the documents here capture how we validate and evolve that posture.

---

## Directory Structure

| Path | Purpose |
|------|---------|
| `docs/security/threat-model.md` | Comprehensive threat scenarios, assets, adversaries, and mitigations across the language and runtime. |
| `docs/security/ocap-guidelines.md` | Best practices for designing, auditing, and testing capability manifests. |
| `docs/security/continuation-hardening.md` | Requirements for secure continuation persistence, encryption, signing, and resumption policies. |
| `docs/security/prompt-safety.md` | Safeguards against prompt-injection, data exfiltration, and semantic manipulation in `prompt` blocks. |
| `docs/security/gem-registry.md` | Supply-chain defenses for the Gem registry, including package signing, provenance tracking, and audit workflows. |
| `docs/security/secure-coding-checklist.md` | Checklist for contributors to validate security requirements before submitting patches. |
| `docs/security/red-team-playbook.md` | Procedures for adversarial testing, including fuzzing, continuation tampering, and capability abuse exercises. |
| `docs/security/incidents.md` | Post-incident reports, remediation tracking, and lessons learned (access-controlled when necessary). |

> **Status:** Some files may be placeholders until corresponding RFCs merge. Update this index whenever new security documents are added.

---

## Security Principles

1. **Least Authority Everywhere**  
   No ambient access: every resource interaction requires an explicit, attenuated capability with verifiable provenance.

2. **Deterministic Surfaces**  
   Security decisions occur at compile time or during deterministic effect dispatch—not in ad-hoc runtime branches.

3. **Defense in Depth**  
   Combine language-level restrictions, Wasm sandboxing, signed continuations, and host-level policies to reduce the blast radius of compromise.

4. **Transparency & Auditability**  
   Every significant security control logs structured events and links to capability manifests, continuation IDs, and module digests.

5. **Rapid Feedback Loops**  
   Automated scanners, fuzzers, and red-team exercises run continuously; regressions block releases.

---

## How to Use This Portal

1. **Start with the Threat Model**  
   Understand the assets Diamond protects (capabilities, continuations, embeddings, user data) and the adversaries we defend against.

2. **Reference Guidelines Per Layer**  
   - Language authors: `ocap-guidelines.md`, `prompt-safety.md`  
   - Runtime engineers: `continuation-hardening.md`, `red-team-playbook.md`  
   - Ecosystem maintainers: `gem-registry.md`, `secure-coding-checklist.md`

3. **Integrate into Development Workflow**  
   - Link relevant security documents in design proposals (`docs/design-decisions/`).  
   - Include checklist items in PR templates and CI validation steps.  
   - Record findings from audits and penetration tests in `incidents.md`.

4. **Update & Version**  
   Changes to security posture require an RFC, explicit risk assessment, and updates to this portal. Increment version history in each document’s changelog section.

---

## Contribution Workflow

1. **Open a Security Issue or RFC**  
   Document motivation, scope, threat impact, and mitigation strategy.

2. **Draft Changes**  
   - Use consistent headings (`Background`, `Controls`, `Monitoring`, `Residual Risk`).  
   - Include diagrams or sequence charts when clarifying data/control flows.  
   - Clearly label normative requirements vs. recommendations.

3. **Peer Review & Sign-Off**  
   - Obtain reviews from the Security working group and affected teams (Runtime, Compiler, Tooling).  
   - Ensure automated security checks (linting, capability scanners, fuzzers) run clean.

4. **Publish & Communicate**  
   - Update indexes and cross-references.  
   - Announce critical changes in release notes and contributor channels.  
   - Schedule follow-up audits if new controls impact runtime behavior or developer workflows.

---

## References & Cross-Links

- `docs/spec/capabilities.md` — Formal capability model and enforcement rules.
- `docs/spec/effects.md` — Effect handling semantics relevant to continuation security.
- `docs/spec/runtime.md` — Runtime requirements for sandboxing, capability validation, and telemetry.
- `docs/architecture/security-threat-model.md` — System architecture view complementing this portal.
- `packages/runtime/` — Reference implementation for capability manager, effect dispatcher, and continuation store.
- `packages/tooling/` — Linting and analysis tools enforcing security constraints.
- `benchmarks/security` (planned) — Performance and resilience tests focused on security-critical paths.

---

## Changelog

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| v0.1 | 2024-XX-XX | _TBD_ | Initial security portal scaffold. |

---

**Mission:** Provide a single source of truth for keeping Diamond “diamond-hard”—resilient, auditable, and safe for autonomous agents operating at scale.