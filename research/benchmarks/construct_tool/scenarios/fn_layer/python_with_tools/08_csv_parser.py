import logging

logger = logging.getLogger(__name__)
CAPABILITIES = {"io.parse": True}
MAX_STEPS = 20000


def solve(text: str) -> list[list[str]]:
    logger.debug("enter solve")
    assert isinstance(text, str)

    lines = [line for line in text.strip().split("\n") if line]
    steps = 0
    out: list[list[str]] = []
    for line in lines:
        steps += 1
        if steps > MAX_STEPS:
            raise RuntimeError("budget_exceeded")
        out.append(line.split(","))

    logger.debug("exit solve rows=%s", len(out))
    return out
