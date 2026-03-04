"""Diamond benchmark reference: JSON parser (simplified).

Program ID: 03
Slug: 03_json_parser_simplified
"""

import json


def solve(text: str) -> tuple[bool, object]:
    try:
        return True, json.loads(text)
    except Exception:
        return False, None
