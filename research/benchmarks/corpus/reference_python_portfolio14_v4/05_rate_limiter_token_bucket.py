"""Diamond portfolio14 reference: token bucket trace output form.

Returns the same output shape as portfolio14 Diamond source:
- each allowed event appends current token count (before decrement)
- each denied event appends False
"""


def solve(events: list[tuple[int, int]], capacity: int, refill_per_sec: int) -> list[object]:
    tokens = capacity
    last_t = 0
    out: list[object] = []

    for t, cost in events:
        dt = max(0, t - last_t)
        tokens = min(capacity, tokens + (dt * refill_per_sec))
        if tokens >= cost:
            out.append(tokens)
            tokens -= cost
        else:
            out.append(False)
        last_t = t

    return out
