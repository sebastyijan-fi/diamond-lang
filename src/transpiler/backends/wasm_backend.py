"""Wasm backend emitter (transitional parity mode).

The current implementation reuses the JS executable lowering as an interoperable
bridge while the native WAT emitter is developed.
"""

from __future__ import annotations

from . import js_backend
from diamond_ir import Program

EXT = ".js"


def emit(program: Program) -> str:
    body = js_backend.emit(program)
    return (
        "// Auto-generated from Diamond IR (Wasm backend parity mode)\n"
        "// This artifact follows the JS executable contract so it can run in a JS host.\n"
        + body
    )
