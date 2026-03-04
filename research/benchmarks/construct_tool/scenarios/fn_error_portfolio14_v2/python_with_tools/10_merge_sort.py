import logging

logger = logging.getLogger(__name__)
MAX_STEPS = 20000


def _merge(left: list[int], right: list[int], steps: list[int]) -> list[int]:
    out: list[int] = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        steps[0] += 1
        if steps[0] > MAX_STEPS:
            raise RuntimeError("budget_exceeded")
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1

    out.extend(left[i:])
    out.extend(right[j:])
    return out


def solve(arr: list[int]) -> list[int]:
    logger.debug("enter solve")
    try:
        assert isinstance(arr, list)
        steps = [0]

        def go(xs: list[int]) -> list[int]:
            steps[0] += 1
            if steps[0] > MAX_STEPS:
                raise RuntimeError("budget_exceeded")
            if len(xs) < 2:
                return xs
            mid = len(xs) // 2
            return _merge(go(xs[:mid]), go(xs[mid:]), steps)

        out = go(arr)
        logger.debug("exit solve size=%s", len(out))
        return out
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/ms: {exc}") from exc
