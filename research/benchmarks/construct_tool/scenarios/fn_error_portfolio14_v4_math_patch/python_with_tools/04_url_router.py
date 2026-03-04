import logging

logger = logging.getLogger(__name__)


def solve(path: str) -> str:
    logger.debug("enter solve path=%s", path)
    try:
        assert isinstance(path, str)
        if path == "/":
            return "home"
        if path == "/users":
            return "users"
        if path == "/health":
            return "ok"
        return "404"
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/router: {exc}") from exc
