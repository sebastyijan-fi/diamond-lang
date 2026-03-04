"""Shared runtime helpers for Python code emitted from Diamond IR."""

from __future__ import annotations

import json
import os
import random
import time
from datetime import date, datetime, time as dt_time_type, timedelta, timezone
from typing import Any, Callable

WILD = object()
RERAISE = object()
TRACE_LOG: list[dict[str, Any]] = []
RESOURCE_COUNTER: dict[str, int] = {}
RESOURCE_LIMIT: int | None = None
CONTROL_TOOLS = {"c", "t", "b", "e"}


def _parse_cap_granted_env(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


CAP_POLICY_MODE = os.environ.get("DIAMOND_CAP_MODE", "allow_all")
if CAP_POLICY_MODE not in {"allow_all", "allow_list"}:
    CAP_POLICY_MODE = "allow_all"
CAP_GRANTED: set[str] = _parse_cap_granted_env(os.environ.get("DIAMOND_CAP_GRANTED", ""))


class IniParseError(Exception):
    path: str
    lineno: int
    msg: str

    def __init__(self, path: str, lineno: int, msg: str) -> None:
        super().__init__(path, lineno, msg)
        self.path = path
        self.lineno = lineno
        self.msg = msg


class DiamondObject:
    __slots__ = ("_shape", "_fields", "_class_name")

    def __init__(self, fields: dict[str, Any], class_name: str | None = None) -> None:
        self._shape = tuple(fields.keys())
        self._fields = dict(fields)
        self._class_name = class_name


class _CapturePattern:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name


def _require_obj(value: Any) -> DiamondObject:
    if not isinstance(value, DiamondObject):
        raise TypeError(f"expected DiamondObject, got {type(value).__name__}")
    return value


def obj_new(fields: dict[str, Any], class_name: str | None = None) -> DiamondObject:
    if not isinstance(fields, dict):
        raise TypeError("obj_new expects dict fields")
    return DiamondObject(fields, class_name=class_name)


def obj_get(obj: Any, name: str) -> Any:
    inst = _require_obj(obj)
    if name not in inst._shape:
        raise AttributeError(f"unknown field: {name}")
    return inst._fields[name]


def obj_set(obj: Any, name: str, value: Any) -> Any:
    inst = _require_obj(obj)
    if name not in inst._shape:
        raise AttributeError(f"unknown field: {name}")
    inst._fields[name] = value
    return value


def obj_is(left: Any, right: Any) -> bool:
    return left is right


def _deep_eq(left: Any, right: Any, seen: set[tuple[int, int]]) -> bool:
    pair = (id(left), id(right))
    if pair in seen:
        return True

    if isinstance(left, DiamondObject) and isinstance(right, DiamondObject):
        seen.add(pair)
        if left._shape != right._shape:
            return False
        for key in left._shape:
            if not _deep_eq(left._fields[key], right._fields[key], seen):
                return False
        return True

    if isinstance(left, dict) and isinstance(right, dict):
        seen.add(pair)
        if set(left.keys()) != set(right.keys()):
            return False
        for key in left:
            if not _deep_eq(left[key], right[key], seen):
                return False
        return True

    if isinstance(left, list) and isinstance(right, list):
        seen.add(pair)
        if len(left) != len(right):
            return False
        return all(_deep_eq(lv, rv, seen) for lv, rv in zip(left, right, strict=True))

    if isinstance(left, tuple) and isinstance(right, tuple):
        seen.add(pair)
        if len(left) != len(right):
            return False
        return all(_deep_eq(lv, rv, seen) for lv, rv in zip(left, right, strict=True))

    return left == right


def obj_eq(left: Any, right: Any) -> bool:
    return _deep_eq(left, right, set())


def CAPTURE(name: str) -> _CapturePattern:
    return _CapturePattern(name)


def obj_invoke(scope: dict[str, Any], obj: Any, name: str, args: list[Any] | None = None) -> Any:
    payload = [] if args is None else args
    if isinstance(obj, DiamondObject):
        if obj._class_name is None:
            raise AttributeError(f"object has no class binding for method {name}")
        sym = f"{obj._class_name}__{name}"
        fn = scope.get(sym)
        if not callable(fn):
            raise AttributeError(f"unknown method {sym}")
        return fn(obj, *payload)
    fn = member(obj, name)
    return fn(*payload)


def midpoint(a: int, b: int) -> int:
    return (a + b) // 2


def idiv(a: int, b: int) -> int:
    if b == 0:
        raise ZeroDivisionError("diamond_runtime.idiv divide by zero")
    return a // b


def left_half(seq: list[Any]) -> list[Any]:
    return seq[: idiv(len(seq), 2)]


def right_half(seq: list[Any]) -> list[Any]:
    return seq[idiv(len(seq), 2) :]


def patch(record: Any, updates: dict[str, Any]) -> Any:
    if isinstance(record, DiamondObject):
        for key, value in updates.items():
            obj_set(record, str(key), value)
        return record
    out = dict(record)
    out.update(updates)
    return out


def member(obj: Any, name: str) -> Any:
    if isinstance(obj, DiamondObject):
        return obj_get(obj, name)
    if isinstance(obj, dict):
        return obj[name]
    return getattr(obj, name)


def index(obj: Any, idx: int) -> Any:
    if isinstance(obj, (list, str, tuple)):
        return obj[idx]
    raise TypeError(f"index expects list/string/tuple, got {type(obj).__name__}")


def match(subject: Any, arms: list[tuple[Any, Callable[..., Any]]]) -> Any:
    for pat, thunk in arms:
        if isinstance(pat, _CapturePattern):
            return thunk(subject)
        if pat is WILD or subject == pat:
            return thunk()
    raise ValueError(f"non-exhaustive match for subject={subject!r}")


def range_inclusive(start: int, end: int) -> list[int]:
    if end < start:
        return []
    return list(range(start, end + 1))


def fold(items: list[Any], init: Any, fn: Callable[[Any, Any], Any]) -> Any:
    acc = init
    for item in items:
        acc = fn(acc, item)
    return acc


def seq(thunks: list[Callable[[], Any]]) -> Any:
    out: Any = None
    for thunk in thunks:
        out = thunk()
    return out


def try_catch(body: Callable[[], Any], handler: Callable[[Exception], Any]) -> Any:
    try:
        return body()
    except Exception as exc:
        out = handler(exc)
        if out is RERAISE:
            raise
        return out


def propagate(value_or_thunk: Any) -> Any:
    try:
        if callable(value_or_thunk):
            return value_or_thunk()
        return value_or_thunk
    except Exception as exc:
        TRACE_LOG.append({"event": "propagate_error", "error": repr(exc)})
        raise


def ln(x: Any) -> int:
    return len(x)


def trim(x: str) -> str:
    return x.strip()


def split(x: str, sep: str) -> list[str]:
    return x.split(sep)


def peek(s: str, i: int, default: Any = None) -> Any:
    if i < 0 or i >= len(s):
        return default
    return s[i]


def take(s: str, i: int, n: int) -> str:
    if n <= 0:
        return ""
    if i < 0:
        i = 0
    if i >= len(s):
        return ""
    return s[i : i + n]


def guard(cond: bool, msg: str, pos: Any = None) -> bool:
    if cond:
        return True
    if pos is None:
        raise RuntimeError(msg)
    raise RuntimeError(f"{msg} @ {pos}")


def put(m: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    out = dict(m)
    out[key] = value
    return out


def get(m: dict[str, Any], key: str, default: Any) -> Any:
    return m.get(key, default)


def del_(m: dict[str, Any], key: str) -> dict[str, Any]:
    out = dict(m)
    out.pop(key, None)
    return out


def to_s(x: Any) -> str:
    return str(x)


def to_i(x: Any) -> int:
    return int(x)


def to_b(x: Any) -> bool:
    return bool(x)


def to_o(x: Any) -> Any:
    return x


def _json_encode_value(value: Any) -> Any:
    if isinstance(value, DiamondObject):
        return {k: _json_encode_value(v) for k, v in value._fields.items()}
    if isinstance(value, dict):
        return {str(k): _json_encode_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_encode_value(v) for v in value]
    if isinstance(value, tuple):
        return [_json_encode_value(v) for v in value]
    return value


def json_dumps(value: Any) -> str:
    payload = _json_encode_value(value)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def json_loads(text: str) -> Any:
    return json.loads(text)


def re_group(match: Any, key: Any = None) -> Any:
    if key is None:
        return match.group()
    if isinstance(key, int):
        return match.groups()[key]
    return match.group(key)


def pad6(text: str) -> str:
    return text.ljust(6, "0")


def parse_int_base(text: str, base: int) -> int:
    return int(text, base)


def dt_date(year: int, month: int, day: int) -> date:
    return date(year, month, day)


def dt_datetime(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    micros: int,
    tz: Any,
) -> datetime:
    return datetime(year, month, day, hour, minute, second, micros, tzinfo=tz)


def dt_time(hour: int, minute: int, second: int, micros: int) -> dt_time_type:
    return dt_time_type(hour, minute, second, micros)


def tz_utc() -> timezone:
    return timezone.utc


def tz_offset(hours: int, minutes: int) -> timezone:
    return timezone(timedelta(hours=hours, minutes=minutes))


def trace_enter(fn_name: str, args: tuple[Any, ...]) -> None:
    TRACE_LOG.append({"event": "enter", "fn": fn_name, "args": args})


def trace_exit(fn_name: str, result: Any) -> None:
    TRACE_LOG.append({"event": "exit", "fn": fn_name, "result": result})


def set_capability_policy(mode: str = "allow_all", granted: list[str] | set[str] | None = None) -> None:
    global CAP_POLICY_MODE, CAP_GRANTED
    if mode not in {"allow_all", "allow_list"}:
        raise ValueError(f"invalid capability mode: {mode}")
    CAP_POLICY_MODE = mode
    CAP_GRANTED = set(granted or [])


def reset_capability_policy() -> None:
    global CAP_POLICY_MODE, CAP_GRANTED
    CAP_POLICY_MODE = "allow_all"
    CAP_GRANTED = set()


def declared_capabilities(declared_tools: list[str]) -> set[str]:
    return {tool for tool in declared_tools if tool not in CONTROL_TOOLS}


def cap_check(fn_name: str, declared_tools: list[str]) -> None:
    required = declared_capabilities(declared_tools)
    if not required:
        return
    if CAP_POLICY_MODE == "allow_all":
        return
    missing = sorted(required - CAP_GRANTED)
    if missing:
        raise PermissionError(
            f"{fn_name}: missing capabilities {missing}; granted={sorted(CAP_GRANTED)}"
        )


def resource_tick(counter: str, amount: int = 1) -> None:
    RESOURCE_COUNTER[counter] = RESOURCE_COUNTER.get(counter, 0) + amount
    if RESOURCE_LIMIT is None:
        return
    total = sum(RESOURCE_COUNTER.values())
    if total > RESOURCE_LIMIT:
        raise RuntimeError(f"resource limit exceeded: {total}>{RESOURCE_LIMIT}")


def with_error_context(exc: Exception, fn_name: str) -> RuntimeError:
    err = RuntimeError(f"{fn_name}: {exc}")
    err.__cause__ = exc
    return err


def call_with(fn: Callable[..., Any], fargs: list[Any] | None, fkwargs: dict[str, Any] | None) -> Any:
    args = fargs if fargs else []
    kwargs = fkwargs if fkwargs else {}
    return fn(*args, **kwargs)


def extern_call(symbol: str, args: list[Any] | None = None) -> Any:
    payload = [] if args is None else args
    raise NotImplementedError(f"external contract stub invoked: {symbol} args={payload!r}")


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def rand_uniform(lo: float, hi: float) -> float:
    return random.uniform(lo, hi)


def is_tuple(value: Any) -> bool:
    return isinstance(value, tuple)


def log_retry_warning(logger: Any, err: Exception, delay: float) -> None:
    if logger is not None:
        logger.warning("%s, retrying in %s seconds...", err, delay)


def make_retry_decorator(
    retry_call_fn: Callable[..., Any],
    exceptions: Any = Exception,
    tries: Any = -1,
    delay: float = 0,
    max_delay: float | None = None,
    backoff: float = 1,
    jitter: Any = 0,
    logger: Any = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return retry_call_fn(
                fn,
                args,
                kwargs,
                exceptions,
                tries,
                delay,
                max_delay,
                backoff,
                jitter,
                logger,
            )

        return wrapped

    return deco


def ini_iscommentline(line: str) -> bool:
    c = line.lstrip()[:1]
    return c in "#;"


def ini_splitlines_keepends(data: str) -> list[str]:
    return data.splitlines(True)


def ini_pair(a: str, b: str | None) -> tuple[str, str | None]:
    return (a, b)


def ini_repr(value: Any) -> str:
    return repr(value)


def ini_raise(path: str, lineno: int, msg: str) -> Any:
    raise IniParseError(path, lineno, msg)


def ini_parseline(
    path: str,
    line: str,
    lineno: int,
    strip_inline_comments: bool,
    strip_section_whitespace: bool,
) -> tuple[str | None, str | None]:
    if ini_iscommentline(line):
        line = ""
    else:
        line = line.rstrip()
    if not line:
        return None, None

    if line[0] == "[":
        realline = line
        for c in "#;":
            line = line.split(c)[0].rstrip()
        if line and line[-1] == "]":
            section_name = line[1:-1]
            if strip_section_whitespace:
                section_name = section_name.strip()
            return section_name, None
        return None, realline.strip()

    if not line[0].isspace():
        try:
            name, value = line.split("=", 1)
            if ":" in name:
                raise ValueError()
        except ValueError:
            try:
                name, value = line.split(":", 1)
            except ValueError:
                raise IniParseError(path, lineno, f"unexpected line: {line!r}") from None

        key_name = name.strip()
        value = value.strip()
        if strip_inline_comments:
            for c in "#;":
                value = value.split(c)[0].rstrip()
        return key_name, value

    line = line.strip()
    if strip_inline_comments:
        for c in "#;":
            line = line.split(c)[0].rstrip()
    return None, line


def ini_parse_lines(
    path: str,
    line_iter: list[str],
    strip_inline_comments: bool = False,
    strip_section_whitespace: bool = False,
) -> list[tuple[int, str | None, str | None, str | None]]:
    result: list[tuple[int, str | None, str | None, str | None]] = []
    section: str | None = None

    for lineno, line in enumerate(line_iter):
        name, data = ini_parseline(path, line, lineno, strip_inline_comments, strip_section_whitespace)

        if name is not None and data is not None:
            result.append((lineno, section, name, data))
        elif name is not None and data is None:
            if not name:
                raise IniParseError(path, lineno, "empty section name")
            section = name
            result.append((lineno, section, None, None))
        elif name is None and data is not None:
            if not result:
                raise IniParseError(path, lineno, "unexpected value continuation")
            last_lineno, last_section, last_name, last_value = result.pop()
            if last_name is None:
                raise IniParseError(path, lineno, "unexpected value continuation")
            if last_value:
                last_value = f"{last_value}\n{data}"
            else:
                last_value = data
            result.append((last_lineno, last_section, last_name, last_value))

    return result


def ini_parse_ini_data(
    path: str,
    data: str,
    strip_inline_comments: bool,
    strip_section_whitespace: bool = False,
) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str | None], int]]:
    tokens = ini_parse_lines(
        path,
        data.splitlines(True),
        strip_inline_comments=strip_inline_comments,
        strip_section_whitespace=strip_section_whitespace,
    )

    sources: dict[tuple[str, str | None], int] = {}
    sections_data: dict[str, dict[str, str]] = {}

    for lineno, section, name, value in tokens:
        if section is None:
            raise IniParseError(path, lineno, "no section header defined")

        sources[(section, name)] = lineno
        if name is None:
            if section in sections_data:
                raise IniParseError(path, lineno, f"duplicate section {section!r}")
            sections_data[section] = {}
        else:
            if name in sections_data[section]:
                raise IniParseError(path, lineno, f"duplicate name {name!r}")
            if value is None:
                raise IniParseError(path, lineno, "missing value")
            sections_data[section][name] = value

    return sections_data, sources
