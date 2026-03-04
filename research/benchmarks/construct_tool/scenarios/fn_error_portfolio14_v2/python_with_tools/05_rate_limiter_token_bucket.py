import logging

logger = logging.getLogger(__name__)
MAX_STEPS = 20000


def solve(events: list[tuple[int, int]], capacity: int, refill_per_sec: int) -> list[bool]:
    logger.debug("enter solve")
    try:
        assert isinstance(events, list)
        assert capacity > 0
        assert refill_per_sec >= 0

        tokens = float(capacity)
        last_t = 0
        out: list[bool] = []
        steps = 0

        for idx, (t, cost) in enumerate(events):
            steps += 1
            if steps > MAX_STEPS:
                raise RuntimeError("budget_exceeded")
            try:
                dt = max(0, t - last_t)
                tokens = min(float(capacity), tokens + (dt * refill_per_sec))
                if tokens >= cost:
                    tokens -= cost
                    out.append(True)
                else:
                    out.append(False)
                last_t = t
            except Exception as op_exc:
                raise RuntimeError(f"event[{idx}] failed") from op_exc

        logger.debug("exit solve")
        return out
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/rl: {exc}") from exc
