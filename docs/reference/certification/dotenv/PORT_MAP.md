# PORT_MAP: python-dotenv -> Diamond (Phase B4)

Status: discovery scaffold.

Planned mapping lanes:
- Lane A (parser/state): parser + variable expansion modules
- Lane B (class/decorator): API facade and decorator-heavy paths
- Lane C (CLI boundary): console entrypoint and subprocess-facing behavior

Language-gate trigger policy:
- Any blocker mapped to: parser ambiguity / missing primitive / runtime contract / backend lowering.
- Promotion only through `docs/decisions/profile_v1/LANGUAGE_CHANGE_GATE.md`.
