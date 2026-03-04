"""Diamond benchmark reference: retry with exponential backoff.

Program ID: 16
Slug: 16_retry_exponential_backoff
"""


def solve(outcomes: list[bool], base_ms: int = 100, max_retries: int = 5) -> tuple[bool, int, list[int]]:
    """Return (ok, tries, waits_ms).

    outcomes[i] indicates whether attempt i succeeds.
    """
    waits: list[int] = []
    attempt = 0

    while attempt <= max_retries:
        ok = attempt < len(outcomes) and outcomes[attempt]
        if ok:
            return True, attempt + 1, waits

        if attempt == max_retries:
            return False, attempt + 1, waits

        waits.append(base_ms * (2**attempt))
        attempt += 1

    return False, max_retries + 1, waits
