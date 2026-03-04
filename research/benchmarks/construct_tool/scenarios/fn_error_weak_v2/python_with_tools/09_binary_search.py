import logging

logger = logging.getLogger(__name__)
MAX_STEPS = 10000


def solve(arr: list[int], target: int) -> int:
    logger.debug("enter solve")
    try:
        assert isinstance(arr, list)
        assert isinstance(target, int)

        lo = 0
        hi = len(arr) - 1
        steps = 0

        while lo <= hi:
            steps += 1
            if steps > MAX_STEPS:
                raise RuntimeError("budget_exceeded")

            mid = (lo + hi) // 2
            if arr[mid] == target:
                return mid
            if arr[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1

        return -1
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/bs: {exc}") from exc
