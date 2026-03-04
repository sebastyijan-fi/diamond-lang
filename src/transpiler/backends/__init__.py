"""Backend registry for Diamond transpiler."""

from __future__ import annotations

from typing import Callable

from diamond_ir import Program

from . import js_backend, python_backend, rust_backend, wasm_backend

Emitter = Callable[[Program], str]

BACKENDS: dict[str, tuple[str, Emitter]] = {
    "python": (python_backend.EXT, python_backend.emit),
    "rust": (rust_backend.EXT, rust_backend.emit),
    "wasm": (wasm_backend.EXT, wasm_backend.emit),
    "js": (js_backend.EXT, js_backend.emit),
}


def get_backend(name: str) -> tuple[str, Emitter]:
    try:
        return BACKENDS[name]
    except KeyError as exc:
        supported = ", ".join(sorted(BACKENDS))
        raise ValueError(f"unknown backend: {name} (supported: {supported})") from exc
