"""Diamond benchmark reference: merge sort.

Program ID: 10
Slug: 10_merge_sort
"""


def _merge(left: list[int], right: list[int]) -> list[int]:
    out: list[int] = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1

    out.extend(left[i:])
    out.extend(right[j:])
    return out


def solve(arr: list[int]) -> list[int]:
    if len(arr) < 2:
        return arr

    mid = len(arr) // 2
    return _merge(solve(arr[:mid]), solve(arr[mid:]))
