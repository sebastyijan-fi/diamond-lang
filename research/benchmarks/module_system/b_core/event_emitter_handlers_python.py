from __future__ import annotations

from collections import defaultdict
from typing import Callable


def core_mk(ev: str, payload: str) -> str:
    return ev + ":" + payload


def core_sub(handler: str, ev: str) -> str:
    return handler + "@" + ev


def handlers_log(ev: str, payload: str) -> str:
    return core_mk(ev, payload)


def handlers_audit(ev: str, payload: str) -> str:
    return "a:" + core_mk(ev, payload)


def handlers_fan(ev: str, payload: str) -> list[str]:
    return [handlers_log(ev, payload), handlers_audit(ev, payload)]


def registry_dispatch(ev: str, payload: str) -> list[str]:
    return handlers_fan(ev, payload)


def registry_routes(ev: str) -> list[str]:
    return [core_sub("log", ev), core_sub("audit", ev)]


def registry_mirror(ev: str, payload: str) -> list[str]:
    return [handlers_log(ev, payload), handlers_audit(ev, payload), core_mk(ev, payload)]


def run_with_callbacks(ev: str, payload: str, callbacks: list[Callable[[str], str]]) -> list[str]:
    hub: dict[str, list[Callable[[str], str]]] = defaultdict(list)
    for cb in callbacks:
        hub[ev].append(cb)
    return [cb(core_mk(ev, payload)) for cb in hub[ev]]
