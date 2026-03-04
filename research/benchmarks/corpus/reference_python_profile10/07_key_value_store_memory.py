"""Diamond benchmark reference: key-value store (in-memory).

Program ID: 07
Slug: 07_key_value_store_memory
"""


def solve(ops: list[tuple[str, str, str]]) -> list[str]:
    store: dict[str, str] = {}
    out: list[str] = []

    for cmd, key, value in ops:
        if cmd == "set":
            store[key] = value
        elif cmd == "get":
            out.append(store.get(key, ""))
        elif cmd == "del":
            store.pop(key, None)

    return out
