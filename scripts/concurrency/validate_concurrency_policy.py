#!/usr/bin/env python3
"""Validate Diamond v1 concurrency policy contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_TOP_LEVEL_KEYS = {
    "language",
    "profile_version",
    "status",
    "concurrency",
    "enforcement",
}


def _iter_inputs(in_path: Path) -> list[Path]:
    if in_path.is_file():
        return [in_path] if in_path.suffix == ".dmd" else []
    return sorted(p for p in in_path.glob("*.dmd") if p.is_file())


def _strip_line_comment_preserve_strings(line: str) -> str:
    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _read_text(path: Path, errors: list[str], label: str) -> str:
    if not path.is_file():
        errors.append(f"{label} missing path: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def _find_keyword_hits(path: Path, banned_tokens: list[str]) -> list[str]:
    errors: list[str] = []
    pattern = re.compile(r"\b(" + "|".join(re.escape(x) for x in banned_tokens) + r")\b")
    for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        code = _strip_line_comment_preserve_strings(raw)
        match = pattern.search(code)
        if match:
            errors.append(f"{path}:{ln}: out-of-profile concurrency token: {match.group(1)}")
    return errors


def validate_policy(
    policy: dict[str, object],
    repo_root: Path,
    input_paths: list[Path],
) -> list[str]:
    errors: list[str] = []

    for key in sorted(REQUIRED_TOP_LEVEL_KEYS):
        if key not in policy:
            errors.append(f"missing top-level key: {key}")
    if errors:
        return errors

    if policy.get("language") != "diamond":
        errors.append("language must be 'diamond'")
    if policy.get("profile_version") != "v1":
        errors.append("profile_version must be 'v1'")
    if policy.get("status") != "stable":
        errors.append("status must be 'stable'")

    concurrency = policy.get("concurrency")
    enforcement = policy.get("enforcement")
    if not isinstance(concurrency, dict):
        errors.append("concurrency must be an object")
        return errors
    if not isinstance(enforcement, dict):
        errors.append("enforcement must be an object")
        return errors

    if concurrency.get("semantic_domain") != "single_thread":
        errors.append("concurrency.semantic_domain must be 'single_thread'")
    if concurrency.get("async_support") != "none":
        errors.append("concurrency.async_support must be 'none'")
    if concurrency.get("memory_ordering") != "none":
        errors.append("concurrency.memory_ordering must be 'none'")
    if concurrency.get("cancellation") != "none":
        errors.append("concurrency.cancellation must be 'none'")
    if concurrency.get("structured_concurrency") is not False:
        errors.append("concurrency.structured_concurrency must be false")

    grammar_ref = enforcement.get("grammar_ref")
    sem_ref = enforcement.get("semantic_contract_ref")
    obj_ref = enforcement.get("object_contract_ref")
    banned_tokens = enforcement.get("banned_tokens")
    for key, ref in (
        ("enforcement.grammar_ref", grammar_ref),
        ("enforcement.semantic_contract_ref", sem_ref),
        ("enforcement.object_contract_ref", obj_ref),
    ):
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"{key} must be a non-empty string")
    if not isinstance(banned_tokens, list) or not banned_tokens:
        errors.append("enforcement.banned_tokens must be a non-empty list")
        return errors
    if not all(isinstance(x, str) and x for x in banned_tokens):
        errors.append("enforcement.banned_tokens must contain non-empty strings")
        return errors

    if errors:
        return errors

    grammar_text = _read_text(repo_root / str(grammar_ref), errors, "enforcement.grammar_ref")
    sem_text = _read_text(repo_root / str(sem_ref), errors, "enforcement.semantic_contract_ref")
    obj_text = _read_text(repo_root / str(obj_ref), errors, "enforcement.object_contract_ref")

    for token in banned_tokens:
        if re.search(r"\b" + re.escape(token) + r"\b", grammar_text, flags=re.IGNORECASE):
            errors.append(f"grammar unexpectedly includes out-of-profile token: {token}")

    if "single-thread semantic domain" not in obj_text:
        errors.append("object contract missing 'single-thread semantic domain' invariant")
    if "Concurrency scope" not in sem_text:
        errors.append("semantic contract missing 'Concurrency scope' section")

    files: list[Path] = []
    for p in input_paths:
        files.extend(_iter_inputs(p))
    files = sorted(set(files))
    for fp in files:
        errors.extend(_find_keyword_hits(fp, banned_tokens))

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Diamond concurrency policy.")
    ap.add_argument("--policy", required=True, help="Path to policy JSON")
    ap.add_argument("--repo-root", default=".", help="Repository root for relative refs")
    ap.add_argument("--in", dest="inputs", action="append", default=[], help="Input .dmd path/dir to check")
    args = ap.parse_args()

    policy_path = Path(args.policy)
    if not policy_path.is_file():
        print(f"error: policy file not found: {policy_path}")
        return 2

    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid json: {exc}")
        return 2

    if not isinstance(policy, dict):
        print("error: policy root must be an object")
        return 2

    input_paths = [Path(p) for p in args.inputs]
    errors = validate_policy(policy, Path(args.repo_root), input_paths)
    if errors:
        print(f"concurrency_policy: FAIL errors={len(errors)}")
        for err in errors:
            print(f"error: {err}")
        return 1

    print("concurrency_policy: OK profile=v1 checks=single_thread+no_async+no_sync_primitives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
