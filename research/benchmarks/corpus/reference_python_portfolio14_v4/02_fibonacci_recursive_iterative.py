"""Diamond portfolio14 reference: Fibonacci (recursive + iterative)."""


def _fib_rec(n: int) -> int:
    if n < 2:
        return n
    return _fib_rec(n - 1) + _fib_rec(n - 2)


def _fib_iter(n: int) -> int:
    a = 0
    b = 1
    i = 0
    while i < n:
        a, b = b, a + b
        i += 1
    return a


def solve(n: int) -> list[int]:
    return [_fib_rec(n), _fib_iter(n)]
