# Diamond V1 Tooling Scope Policy

Status: normative for V1 profile behavior.

This policy fixes tooling integration scope for V1 and prevents accidental claims beyond current guarantees.

## 1. Out-of-profile tooling integrations

- LSP integration is out-of-profile in V1.
- Interactive debugger integration is out-of-profile in V1.
- Profiler integration is out-of-profile in V1.

## 2. Enforcement model

- Scope is machine-validated via `scripts/scope/validate_scope_policy.py`.
- Policy regressions are covered by `scripts/scope/validate_scope_policy_tests.py`.
- CI gate integration is via `scripts/ci/validate_v1_gates.sh`.
