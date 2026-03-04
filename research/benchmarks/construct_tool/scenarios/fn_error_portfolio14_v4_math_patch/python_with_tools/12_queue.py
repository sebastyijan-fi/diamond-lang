import logging

logger = logging.getLogger(__name__)
MAX_STEPS = 20000


def solve(ops: list[tuple[str, int]]) -> list[int]:
    logger.debug("enter solve")
    try:
        assert isinstance(ops, list)
        q: list[int] = []
        out: list[int] = []

        steps = 0
        for idx, (cmd, value) in enumerate(ops):
            steps += 1
            if steps > MAX_STEPS:
                raise RuntimeError("budget_exceeded")
            try:
                if cmd == "enq":
                    q.append(value)
                elif cmd == "deq" and q:
                    out.append(q.pop(0))
            except Exception as op_exc:
                raise RuntimeError(f"op[{idx}] failed") from op_exc

        logger.debug("exit solve out=%s", len(out))
        return out
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/queue: {exc}") from exc
