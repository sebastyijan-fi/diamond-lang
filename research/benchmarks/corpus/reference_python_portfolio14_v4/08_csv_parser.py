"""Diamond benchmark reference: CSV parser (simple).

Program ID: 08
Slug: 08_csv_parser
"""


def solve(text: str) -> list[list[str]]:
    # portfolio14_v4 mirrors the minimal Diamond semantics:
    # no trimming, no filtering of trailing empty lines.
    lines = text.split("\n")
    return [line.split(",") for line in lines]
