import logging

logger = logging.getLogger(__name__)
CAPABILITIES = {"net.route": False}
MAX_STEPS = 32


def solve(path: str) -> str:
    logger.debug("enter solve path=%s", path)
    assert isinstance(path, str)

    steps = 0
    if path == "/":
        steps += 1
        if steps > MAX_STEPS:
            raise RuntimeError("budget_exceeded")
        logger.debug("exit solve route=home")
        return "home"

    if path == "/users":
        logger.debug("exit solve route=users")
        return "users"

    if path == "/health":
        logger.debug("exit solve route=ok")
        return "ok"

    logger.debug("exit solve route=404")
    return "404"
