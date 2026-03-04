"""Diamond benchmark reference: Fibonacci (recursive + iterative).

Program ID: 02
Slug: 02_fibonacci_recursive_iterative
"""


def fib_rec(n: int) -> int:
    if n < 2:
        return n
    return fib_rec(n - 1) + fib_rec(n - 2)


def fib_iter(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def solve(n: int) -> tuple[int, int]:
    return fib_rec(n), fib_iter(n)
