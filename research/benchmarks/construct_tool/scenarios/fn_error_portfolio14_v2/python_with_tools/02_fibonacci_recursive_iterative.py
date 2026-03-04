import logging

logger = logging.getLogger(__name__)
MAX_STEPS = 20000


def solve(n: int) -> tuple[int, int]:
    logger.debug("enter solve n=%s", n)
    try:
        assert isinstance(n, int)
        assert n >= 0
        steps = [0]

        def fib_rec(x: int) -> int:
            steps[0] += 1
            if steps[0] > MAX_STEPS:
                raise RuntimeError("budget_exceeded")
            if x < 2:
                return x
            return fib_rec(x - 1) + fib_rec(x - 2)

        a = 0
        b = 1
        for _ in range(n):
            steps[0] += 1
            if steps[0] > MAX_STEPS:
                raise RuntimeError("budget_exceeded")
            a, b = b, a + b

        out = (fib_rec(n), a)
        logger.debug("exit solve")
        return out
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/fib: {exc}") from exc
