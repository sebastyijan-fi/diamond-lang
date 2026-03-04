"""Diamond benchmark reference: FizzBuzz.

Program ID: 01
Slug: 01_fizzbuzz
"""


def solve(n: int) -> list[str]:
    """Return FizzBuzz values for 1..n inclusive."""
    if n < 1:
        return []

    out: list[str] = []
    for i in range(1, n + 1):
        div3 = (i % 3) == 0
        div5 = (i % 5) == 0

        if div3 and div5:
            out.append("FizzBuzz")
        elif div3:
            out.append("Fizz")
        elif div5:
            out.append("Buzz")
        else:
            out.append(str(i))

    return out
