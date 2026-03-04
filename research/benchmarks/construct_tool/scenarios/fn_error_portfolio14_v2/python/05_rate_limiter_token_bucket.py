"""Diamond benchmark reference: Rate limiter (token bucket).

Program ID: 05
Slug: 05_rate_limiter_token_bucket
"""


def solve(events: list[tuple[int, int]], capacity: int, refill_per_sec: int) -> list[bool]:
    tokens = float(capacity)
    last_t = 0
    out: list[bool] = []

    for t, cost in events:
        dt = max(0, t - last_t)
        tokens = min(float(capacity), tokens + (dt * refill_per_sec))
        if tokens >= cost:
            tokens -= cost
            out.append(True)
        else:
            out.append(False)
        last_t = t

    return out
