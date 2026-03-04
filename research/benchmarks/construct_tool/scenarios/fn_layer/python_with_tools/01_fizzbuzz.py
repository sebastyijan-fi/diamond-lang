import logging

logger = logging.getLogger(__name__)
CAPABILITIES = {"cpu.loop": True}
MAX_STEPS = 10000


def solve(n: int) -> list[str]:
    logger.debug("enter solve n=%s", n)
    assert isinstance(n, int)
    assert n >= 0

    steps = 0
    out: list[str] = []
    for i in range(1, n + 1):
        steps += 1
        if steps > MAX_STEPS:
            raise RuntimeError("budget_exceeded")

        if i % 15 == 0:
            out.append("FizzBuzz")
        elif i % 3 == 0:
            out.append("Fizz")
        elif i % 5 == 0:
            out.append("Buzz")
        else:
            out.append(str(i))

    logger.debug("exit solve size=%s", len(out))
    return out
