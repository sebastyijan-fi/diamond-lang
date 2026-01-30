# std-unit Module Guidance

## Purpose
The `packages/stdlib/std-unit/` module provides Diamond's foundational unit types, refinement type primitives, and semantic type utilities. This module establishes the building blocks for type-safe, semantically-rich agent development. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, semantic type philosophy, and capability discipline.
- **`diamond2.md`** — Architectural feasibility, type system integration, and verification strategies.
- **`diamond3.md`** — Grammar, semantic typing with refinements, and constrained decoding integration.

The `std-unit` module is where Diamond's type system meets practical utility—providing validated, constrained types that collapse hallucinations at compile-time.

---

## Directory Contract

| Path | Purpose |
| --- | --- |
| `src/lib.dm` | Module root, public exports. |
| `src/primitives.dm` | Core refinement type definitions (Email, Url, etc.). |
| `src/numeric.dm` | Numeric refinement types (PositiveInt, Percentage, etc.). |
| `src/text.dm` | Text-based refinement types and validators. |
| `src/temporal.dm` | Time and date refinement types. |
| `src/identifiers.dm` | ID types (UUID, semantic identifiers). |
| `src/validators.dm` | Validation predicates and constraint functions. |
| `src/conversions.dm` | Type conversion utilities and coercions. |
| `capabilities.toml` | Capability manifest (typically none required). |
| `tests/` | Comprehensive test suites. |
| `examples/` | Usage demonstrations. |
| `README.md` | Module documentation and API reference. |
| `GUIDANCE.md` | This file—contribution and quality standards. |

---

## Core Type Categories

### Textual Refinements

| Type | Base | Constraint | Use Case |
| --- | --- | --- | --- |
| `Email` | `String` | Valid email format | User contact, notifications |
| `Url` | `String` | Valid URL format | API endpoints, links |
| `PhoneNumber` | `String` | E.164 format | Communication |
| `NonEmptyString` | `String` | Length > 0 | Required fields |
| `TrimmedString` | `String` | No leading/trailing whitespace | Clean input |
| `Slug` | `String` | URL-safe identifier | URLs, keys |
| `Markdown` | `String` | Valid Markdown | Documentation, content |
| `Json` | `String` | Valid JSON | Data interchange |

### Numeric Refinements

| Type | Base | Constraint | Use Case |
| --- | --- | --- | --- |
| `PositiveInt` | `Int` | > 0 | Counts, IDs |
| `NonNegativeInt` | `Int` | >= 0 | Indices, quantities |
| `NegativeInt` | `Int` | < 0 | Deltas, offsets |
| `Percentage` | `Float` | 0.0 <= x <= 100.0 | Rates, progress |
| `Probability` | `Float` | 0.0 <= x <= 1.0 | ML scores, likelihoods |
| `NonZeroInt` | `Int` | != 0 | Divisors, multipliers |
| `BoundedInt[MIN, MAX]` | `Int` | MIN <= x <= MAX | Ranges, limits |
| `BoundedFloat[MIN, MAX]` | `Float` | MIN <= x <= MAX | Continuous ranges |

### Identifier Types

| Type | Base | Constraint | Use Case |
| --- | --- | --- | --- |
| `Uuid` | `String` | Valid UUID v4 | Unique identifiers |
| `Ulid` | `String` | Valid ULID | Sortable identifiers |
| `Base64` | `String` | Valid Base64 | Encoded data |
| `Hex` | `String` | Valid hexadecimal | Hashes, colors |
| `SemanticVersion` | `String` | Valid semver | Versioning |

### Temporal Refinements

| Type | Base | Constraint | Use Case |
| --- | --- | --- | --- |
| `Timestamp` | `Int` | Unix epoch milliseconds | Event times |
| `IsoDate` | `String` | ISO 8601 date | Date storage |
| `IsoDateTime` | `String` | ISO 8601 datetime | Datetime storage |
| `Duration` | `Int` | Milliseconds >= 0 | Time spans |
| `FutureTimestamp` | `Timestamp` | > now() | Scheduling |
| `PastTimestamp` | `Timestamp` | < now() | Historical data |

---

## Type Definition Patterns

### Basic Refinement Type

```diamond
/// An email address validated for RFC 5322 format.
///
/// @stability stable
/// @since 0.1.0
type Email = String where { valid_email }

/// Validate an email address format.
fn valid_email(s: String) -> Bool {
    // RFC 5322 simplified validation
    s.contains("@") && s.length() > 3
}
```

### Parameterized Refinement Type

```diamond
/// An integer bounded within a specified range.
///
/// @stability stable
/// @since 0.1.0
type BoundedInt[MIN: Int, MAX: Int] = Int where { 
    >= MIN, <= MAX 
}

// Usage
type Age = BoundedInt[0, 150]
type HttpStatus = BoundedInt[100, 599]
```

### Composite Refinement Type

```diamond
/// A valid HTTP URL (http:// or https://).
///
/// @stability stable
/// @since 0.1.0
type HttpUrl = Url where { 
    starts_with("http://") || starts_with("https://") 
}
```

---

## Validation Predicates

### Predicate Conventions

1. **Pure Functions**: Validators must be pure—no side effects.
2. **Deterministic**: Same input always produces same result.
3. **Documented**: Explain what the predicate validates.
4. **Tested**: Include edge cases and boundary conditions.

### Predicate API

```diamond
/// Validate that a string is a properly formatted email.
///
/// Validates against a simplified RFC 5322 pattern.
/// Does not verify that the email actually exists.
///
/// # Examples
/// ```diamond
/// valid_email("user@example.com")  // true
/// valid_email("invalid")           // false
/// ```
fn valid_email(s: String) -> Bool { ... }

/// Validate that a string is a properly formatted URL.
///
/// Supports http, https, ftp, and file schemes.
fn valid_url(s: String) -> Bool { ... }

/// Validate that a string is valid JSON.
fn valid_json(s: String) -> Bool { ... }

/// Validate that a string is a valid UUID v4.
fn valid_uuid(s: String) -> Bool { ... }
```

---

## Conversion Utilities

### Safe Conversions

```diamond
/// Attempt to parse a string as an Email.
///
/// Returns `None` if the string is not a valid email format.
fn try_email(s: String) -> Option[Email] {
    if valid_email(s) {
        Some(Email(s))
    } else {
        None
    }
}

/// Parse a string as an Email, or return an error.
fn parse_email(s: String) -> Result[Email, ValidationError] {
    if valid_email(s) {
        Ok(Email(s))
    } else {
        Err(ValidationError::InvalidFormat("email", s))
    }
}
```

### Coercion Utilities

```diamond
/// Trim whitespace and convert to TrimmedString.
fn to_trimmed(s: String) -> TrimmedString {
    TrimmedString(s.trim())
}

/// Clamp an integer to a bounded range.
fn clamp_int[MIN: Int, MAX: Int](value: Int) -> BoundedInt[MIN, MAX] {
    BoundedInt(max(MIN, min(MAX, value)))
}
```

---

## Capability Requirements

The `std-unit` module is designed to be **capability-free**:

```toml
# capabilities.toml
[module]
name = "std-unit"
version = "0.1.0"
stability = "stable"

# No capabilities required - all operations are pure
[required_capabilities]
# (none)

[notes]
description = """
All types and functions in std-unit are pure and require no capabilities.
This makes the module safe to use in any context without security concerns.
"""
```

---

## Integration with Constrained Decoding

`std-unit` types are designed for seamless constrained decoding integration:

```diamond
/// LLM response with semantic type constraints.
fn get_user_email() -> Email performs LLM {
    // Constrained decoding ensures valid Email format
    perform LLM.complete[Email](
        "Extract the user's email address from the conversation."
    )
}
```

The refinement constraints are used to:
1. Generate grammar constraints for LLM output.
2. Validate responses at decode time.
3. Guarantee type-safe results without post-validation.

---

## Testing Standards

### Unit Tests

Test each refinement type:

```diamond
test "Email accepts valid formats" {
    assert valid_email("user@example.com")
    assert valid_email("name+tag@domain.co.uk")
    assert valid_email("a@b.c")
}

test "Email rejects invalid formats" {
    assert !valid_email("")
    assert !valid_email("no-at-sign")
    assert !valid_email("@no-local-part.com")
    assert !valid_email("no-domain@")
}
```

### Property Tests

Verify refinement invariants:

```diamond
property "PositiveInt is always > 0" {
    forall (n: PositiveInt) {
        n.value() > 0
    }
}

property "Percentage is within bounds" {
    forall (p: Percentage) {
        p.value() >= 0.0 && p.value() <= 100.0
    }
}

property "Email round-trips through parsing" {
    forall (e: Email) {
        parse_email(e.to_string()) == Ok(e)
    }
}
```

### Edge Case Tests

```diamond
test "BoundedInt boundary conditions" {
    let min_age: Age = Age(0)
    let max_age: Age = Age(150)
    
    assert try_bounded_int[0, 150](-1) == None
    assert try_bounded_int[0, 150](151) == None
    assert try_bounded_int[0, 150](0) == Some(Age(0))
    assert try_bounded_int[0, 150](150) == Some(Age(150))
}
```

---

## Documentation Standards

### Type Documentation

```diamond
/// A percentage value between 0 and 100 inclusive.
///
/// Represents a proportion as a human-friendly percentage rather than
/// a decimal fraction. Use `Probability` for 0-1 range values.
///
/// # Constraints
/// * Value >= 0.0
/// * Value <= 100.0
///
/// # Examples
/// ```diamond
/// let progress: Percentage = Percentage(75.5)
/// let rate: Percentage = parse_percentage("42.0")?
/// ```
///
/// # See Also
/// * `Probability` - For 0-1 range values
/// * `BoundedFloat` - For custom ranges
///
/// @stability stable
/// @since 0.1.0
type Percentage = Float where { >= 0.0, <= 100.0 }
```

### Function Documentation

```diamond
/// Convert a probability (0-1) to a percentage (0-100).
///
/// # Arguments
/// * `p` - A probability value between 0 and 1.
///
/// # Returns
/// The equivalent percentage value.
///
/// # Examples
/// ```diamond
/// let pct = probability_to_percentage(Probability(0.75))
/// assert pct == Percentage(75.0)
/// ```
///
/// @stability stable
/// @since 0.1.0
fn probability_to_percentage(p: Probability) -> Percentage {
    Percentage(p.value() * 100.0)
}
```

---

## Quality Checklist (Pre-Merge)

- [ ] Type has comprehensive doc comment with examples.
- [ ] Validation predicate is pure and deterministic.
- [ ] Unit tests cover valid and invalid cases.
- [ ] Property tests verify refinement invariants.
- [ ] Edge cases and boundary conditions tested.
- [ ] Conversion utilities provided (`try_*`, `parse_*`).
- [ ] No capabilities required (pure module).
- [ ] Integrates with constrained decoding patterns.
- [ ] README updated with new types.
- [ ] Stability annotation included.

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the new type.
   - Justify the semantic value of the refinement.
   - Provide use cases and examples.
   - Consider overlap with existing types.

2. **Implementation**
   - Define type with `where` constraints.
   - Implement validation predicate.
   - Add conversion utilities.
   - Write comprehensive tests.

3. **Review**
   - Verify predicate correctness.
   - Check documentation completeness.
   - Ensure constrained decoding compatibility.
   - Validate no capability requirements.

4. **Publication**
   - Export from `lib.dm`.
   - Update README type index.
   - Add CHANGELOG entry.

---

## Future Enhancements

- Type-level arithmetic for compile-time bounds checking.
- Automatic grammar generation for constrained decoding.
- Refinement type composition operators.
- Runtime refinement type reflection.
- Custom error messages per refinement failure.
- Localized validation (country-specific formats).

---

The `std-unit` module is Diamond's type safety foundation. Every refinement type added here helps prevent runtime errors and reduces hallucination surface area. Build types that are precise, well-documented, and practically useful for agent development.