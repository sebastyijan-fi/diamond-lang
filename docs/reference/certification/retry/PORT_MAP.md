# Port Map: `invl/retry` -> Diamond

## Scope v0

Target parity for first pass:

- `retry.api.retry_call` (core)
- `retry.api.retry` (decorator API via HOF wrapper)
- `retry.api.__retry_internal` (compat wrapper)

## Behavior checklist

From upstream `retry/api.py`:

1. Retry loop while `tries` is truthy.
2. On success: return function result immediately.
3. On caught exception:
   - decrement remaining tries
   - if exhausted, re-raise
   - optional logger warning
   - sleep current delay
   - multiply delay by backoff
   - add jitter (fixed or random range)
   - cap with `max_delay` if configured

## Diamond construct mapping

- Loop: `while _tries`
- Branching: `case` / conditional arms
- Error propagation and context: map exception path to Diamond error model
- Arithmetic: `*`, `+`, `min`
- External boundary effects:
  - `sleep` (time effect)
  - random jitter (random effect)
  - logger warning (log effect)

## Known semantic gaps to close

Closed in current v0 port:

1. Exception tuple/dynamic matching (`isexc(e, exceptions)` -> `isinstance` lowering)
2. Re-raise semantics preserving original traceback (`reraise` + runtime bare `raise`)
3. Random jitter path (`rnd(lo, hi)` + tuple detection)
4. Decorator adapter (`retry`) via HOF (`mk_retry(...)`)
