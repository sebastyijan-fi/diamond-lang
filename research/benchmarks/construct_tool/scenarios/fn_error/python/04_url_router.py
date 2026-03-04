"""Diamond benchmark reference: URL router.

Program ID: 04
Slug: 04_url_router
"""


def solve(path: str) -> str:
    if path == "/":
        return "home"
    if path == "/users":
        return "users"
    if path == "/health":
        return "ok"
    return "404"
