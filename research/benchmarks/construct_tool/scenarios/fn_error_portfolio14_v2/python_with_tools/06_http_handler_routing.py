import logging

logger = logging.getLogger(__name__)


def solve(method: str, path: str) -> tuple[int, dict[str, object]]:
    logger.debug("enter solve method=%s path=%s", method, path)
    try:
        assert isinstance(method, str)
        assert isinstance(path, str)

        if method != "GET":
            return 405, {"error": "method not allowed"}

        if path == "/users":
            return 200, {"users": ["u1", "u2"]}

        if path == "/health":
            return 200, {"status": "ok"}

        return 404, {"error": "not found"}
    except Exception as exc:
        logger.exception("solve failed")
        raise RuntimeError(f"solve/http: {exc}") from exc
