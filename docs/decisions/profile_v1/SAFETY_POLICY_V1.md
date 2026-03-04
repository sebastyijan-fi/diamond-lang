# Diamond V1 Safety Policy

Status: normative for V1 profile behavior.

## Scope

This policy defines the enforced baseline for null handling, numeric safety, and bounds behavior in Diamond V1.

## 1. Null and missing access

- `none` is the only null/absence literal in Diamond source.
- Concrete typed values are non-null by default; assigning `none` to non-unit types is a static type error.
- Byte-typed values are statically constrained by literal inference to the `0..255` range in V1.
- Accessing missing closed-shape object fields is invalid.
- Static analyzer rejects statically provable unknown member reads/writes.
- Runtime rejects unresolved unknown member reads/writes.

## 2. Division and modulo by zero

- Division or modulo by a literal zero is a compile-time error.
- Dynamic division/modulo by zero is a runtime error.

## 3. Bounds policy

- Indexing uses bounds checks.
- Out-of-bounds index operations are runtime errors.
- Static analyzer rejects obvious out-of-bounds indexing on list/string literals.

## 4. Numeric overflow policy (V1)

- V1 numeric semantics are host-runtime numeric semantics.
- No additional overflow wrapping/saturation layer is inserted in V1.
- Backend differences are tracked for V2 tightening.

## 5. Unsafe/audit boundary

- Diamond source has no explicit unsafe escape hatch in V1.
- Host/runtime interop calls are considered trusted boundaries and must be audited in backend/runtime code.

## 6. Conformance anchors

- `src/transpiler/semantic_validate.py`
- `src/transpiler/semantic_validation_tests.py`
- `src/transpiler/runtime/diamond_runtime.py`
- `src/transpiler/runtime/diamond_runtime.js`
- `src/transpiler/runtime/diamond_runtime.rs`
- `src/conformance/cases/runtime_v0_core.json`
- `src/conformance/run_stdlib_conformance.py`
