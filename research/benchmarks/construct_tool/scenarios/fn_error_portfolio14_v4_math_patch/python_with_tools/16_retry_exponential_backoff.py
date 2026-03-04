import logging

logger = logging.getLogger(__name__)
MAX_STEPS = 4096


def solve(outcomes: list[bool], base_ms: int = 100, max_retries: int = 5) -> tuple[bool, int, list[int]]:
    logger.debug("enter solve")
    try:
        assert isinstance(outcomes, list)
        assert base_ms > 0
        assert max_retries >= 0

        waits: list[int] = []
        attempt = 0
        steps = 0
        while attempt <= max_retries:
            steps += 1
            if steps > MAX_STEPS:
                raise RuntimeError("budget_exceeded")

            ok = attempt < len(outcomes) and outcomes[attempt]
            if ok:
                return True, attempt + 1, waits

            if attempt == max_retries:
                return False, attempt + 1, waits

            waits.append(base_ms * (2**attempt))
            attempt += 1

        return False, max_retries + 1, waits
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/retry: {exc}") from exc
