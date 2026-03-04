from __future__ import annotations

import json


def storage_empty() -> dict[str, str]:
    return {}


def storage_put(st: dict[str, str], k: str, v: str) -> dict[str, str]:
    out = dict(st)
    out[k] = v
    return out


def storage_delk(st: dict[str, str], k: str) -> dict[str, str]:
    out = dict(st)
    out.pop(k, None)
    return out


def storage_getk(st: dict[str, str], k: str) -> str:
    return st.get(k, "")


def serializer_pack(st: dict[str, str]) -> str:
    return json.dumps(st, sort_keys=True)


def serializer_unpack(raw: str) -> dict[str, str]:
    if not raw:
        return {}
    return json.loads(raw)


def serializer_key(k: str) -> str:
    return "k:" + k


def api_set(st: dict[str, str], k: str, v: str) -> dict[str, str]:
    return storage_put(st, serializer_key(k), v)


def api_drop(st: dict[str, str], k: str) -> dict[str, str]:
    return storage_delk(st, serializer_key(k))


def api_fetch(st: dict[str, str], k: str) -> str:
    return storage_getk(st, serializer_key(k))


def api_round(st: dict[str, str]) -> dict[str, str]:
    return serializer_unpack(serializer_pack(st))
