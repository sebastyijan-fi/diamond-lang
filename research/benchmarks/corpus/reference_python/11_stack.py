"""Diamond benchmark reference: stack implementation.

Program ID: 11
Slug: 11_stack
"""


def solve(ops: list[tuple[str, int]]) -> list[int]:
    stack: list[int] = []
    out: list[int] = []

    for cmd, value in ops:
        if cmd == "push":
            stack.append(value)
        elif cmd == "pop" and stack:
            out.append(stack.pop())

    return out
