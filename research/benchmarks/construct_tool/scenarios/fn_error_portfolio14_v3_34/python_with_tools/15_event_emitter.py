import logging

logger = logging.getLogger(__name__)
MAX_STEPS = 20000


def solve(ops: list[tuple[str, str, str]]) -> list[str]:
    logger.debug("enter solve")
    try:
        assert isinstance(ops, list)
        handlers: dict[str, list[str]] = {}
        out: list[str] = []

        steps = 0
        for idx, (cmd, event, value) in enumerate(ops):
            steps += 1
            if steps > MAX_STEPS:
                raise RuntimeError("budget_exceeded")

            try:
                if cmd == "on":
                    handlers.setdefault(event, []).append(value)
                elif cmd == "emit":
                    out.extend(handlers.get(event, []))
            except Exception as op_exc:
                raise RuntimeError(f"op[{idx}] failed") from op_exc

        logger.debug("exit solve out=%s", len(out))
        return out
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/emitter: {exc}") from exc
