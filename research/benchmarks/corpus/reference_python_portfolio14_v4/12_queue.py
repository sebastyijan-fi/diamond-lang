"""Diamond portfolio14 reference: queue operations."""


def solve(ops: list[tuple[str, int]]) -> list[int]:
    q: list[int] = []
    out: list[int] = []
    for cmd, value in ops:
        if cmd == "enq":
            q.append(value)
        elif cmd == "deq" and q:
            out.append(q.pop(0))
    return out
