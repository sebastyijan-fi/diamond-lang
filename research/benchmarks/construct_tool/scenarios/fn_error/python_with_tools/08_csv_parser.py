import logging

logger = logging.getLogger(__name__)


def solve(text: str) -> list[list[str]]:
    logger.debug("enter solve")
    try:
        assert isinstance(text, str)
        lines = [line for line in text.strip().split("\n") if line]
        out: list[list[str]] = []
        for idx, line in enumerate(lines):
            try:
                out.append(line.split(","))
            except Exception as row_exc:
                raise RuntimeError(f"row[{idx}] parse failed") from row_exc
        logger.debug("exit solve rows=%s", len(out))
        return out
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/csv: {exc}") from exc
