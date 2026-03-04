"""Diamond benchmark reference: HTTP handler with routing.

Program ID: 06
Slug: 06_http_handler_routing
"""


def solve(method: str, path: str) -> tuple[int, dict[str, object]]:
    if method != "GET":
        return 405, {"error": "method not allowed"}

    if path == "/users":
        return 200, {"users": ["u1", "u2"]}

    if path == "/health":
        return 200, {"status": "ok"}

    return 404, {"error": "not found"}
