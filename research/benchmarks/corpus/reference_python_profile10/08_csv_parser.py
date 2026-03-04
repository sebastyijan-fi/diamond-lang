"""Diamond benchmark reference: CSV parser (simple).

Program ID: 08
Slug: 08_csv_parser
"""


def solve(text: str) -> list[list[str]]:
    lines = [line for line in text.strip().split("\n") if line]
    return [line.split(",") for line in lines]
