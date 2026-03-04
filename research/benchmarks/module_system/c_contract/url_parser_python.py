from __future__ import annotations

from urllib.parse import unquote


def types_trim_slash(s: str) -> str:
    return s[:-1] if len(s) > 0 and s[-1] == "/" else s


def types_is_abs(s: str) -> bool:
    return len(s) > 0 and s[0] == "/"


def types_as_i(s: str) -> int:
    return int(s)


def scanner_norm_path(p: str) -> str:
    return types_trim_slash(unquote(p.strip()))


def scanner_abs_path(p: str) -> bool:
    return types_is_abs(p)


def scanner_segs(p: str) -> list[str]:
    return scanner_norm_path(p).split("/")


def scanner_first(p: str) -> str:
    segs = scanner_segs(p)
    return "" if len(segs) == 0 else segs[0]


def scanner_last(p: str) -> str:
    segs = scanner_segs(p)
    return "" if len(segs) == 0 else segs[len(segs) - 1]


def scanner_seg_count(p: str) -> int:
    return types_as_i(str(len(scanner_segs(p))))


def parser_parse(p: str) -> dict[str, object]:
    segs = scanner_segs(p)
    return {
        "abs": scanner_abs_path(p),
        "n": len(segs),
        "h": scanner_first(p),
        "t": scanner_last(p),
        "i": scanner_seg_count(p),
    }
