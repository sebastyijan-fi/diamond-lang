"""Diamond benchmark reference: event emitter.

Program ID: 15
Slug: 15_event_emitter
"""


def solve(ops: list[tuple[str, str, str]]) -> list[str]:
    handlers: dict[str, list[str]] = {}
    out: list[str] = []

    for cmd, event, value in ops:
        if cmd == "on":
            handlers.setdefault(event, []).append(value)
        elif cmd == "emit":
            out.extend(handlers.get(event, []))

    return out
