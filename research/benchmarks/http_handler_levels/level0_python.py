from http import Request, Response, json_response


def handle(request: Request) -> Response:
    if request.method == "GET":
        if request.path == "/users":
            users = get_all_users()
            return json_response(200, users)
        elif request.path == "/health":
            return json_response(200, {"status": "ok"})
        else:
            return json_response(404, {"error": "not found"})
    else:
        return json_response(405, {"error": "method not allowed"})
