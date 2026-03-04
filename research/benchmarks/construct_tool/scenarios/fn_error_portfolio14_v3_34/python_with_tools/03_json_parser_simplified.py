import json
import logging

logger = logging.getLogger(__name__)


def solve(text: str) -> tuple[bool, object]:
    logger.debug("enter solve")
    try:
        assert isinstance(text, str)
        try:
            out = json.loads(text)
            logger.debug("exit solve ok")
            return True, out
        except Exception as parse_exc:
            logger.debug("parse failed")
            raise RuntimeError("json_parse_failed") from parse_exc
    except Exception as exc:
        return False, {"err": str(exc)}
