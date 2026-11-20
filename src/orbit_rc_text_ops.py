"""Bounded, exact block-edit helpers for Orbit Remote Commander.

Adapted from the line-ending detection/normalization and exact replacement
approach in wonderwhy-er/DesktopCommanderMCP, MIT licensed.
Upstream: https://github.com/wonderwhy-er/DesktopCommanderMCP
Pinned source commit: 9a101b17e44577f0baefa4c7120f087881c5cc56
Upstream files: src/utils/lineEndingHandler.ts, src/tools/edit.ts.
Copyright (c) 2024-2025 Eduard Ruzga and Desktop Commander Contributors.
Full MIT license: THIRD_PARTY_NOTICES.md (repository root and deployed alongside executor)

This is a deliberately reduced, fail-closed Python adaptation: no fuzzy
matching, no whole-disk access, and no standalone authorization mechanism.
"""
from __future__ import annotations

import os


class BlockEditError(ValueError):
    """Unsafe or ambiguous exact-match block edit."""


def detect_line_ending(content: str) -> str:
    """Preserve first observed CRLF/LF/CR style, like Desktop Commander's helper."""
    for i, char in enumerate(content):
        if char == "\r":
            return "\r\n" if content[i:i + 2] == "\r\n" else "\r"
        if char == "\n":
            return "\n"
    return os.linesep


def normalize_line_endings(text: str, target: str) -> str:
    """Port of DesktopCommander's normalization order for exact replacements."""
    if target not in ("\r\n", "\n", "\r"):
        raise BlockEditError("Unsupported target newline style")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if target == "\r\n":
        return normalized.replace("\n", "\r\n")
    if target == "\r":
        return normalized.replace("\n", "\r")
    return normalized


def exact_block_replacement(
    content: str,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1,
    *,
    max_bytes: int = 96_000,
) -> dict:
    """Return a bounded preview/result, never write to disk.

    Exact, non-overlapping occurrence count must equal expected_replacements.
    A fuzzy near-match must NOT silently change a different source location.
    """
    if not isinstance(content, str):
        raise BlockEditError("Only UTF-8 text supported")
    if not isinstance(old_string, str) or not old_string:
        raise BlockEditError("Search string must be non-empty text")
    if not isinstance(new_string, str):
        raise BlockEditError("Replacement must be text")
    if type(expected_replacements) is not int or not 1 <= expected_replacements <= 8:
        raise BlockEditError("Expected replacements must be an integer from 1 to 8")
    if len(old_string.encode("utf-8")) > 16_384 or len(new_string.encode("utf-8")) > 16_384:
        raise BlockEditError("Search/replacement block exceeds 16 KB")
    if len(content.encode("utf-8")) > max_bytes:
        raise BlockEditError("File exceeds edit limit")

    newline = detect_line_ending(content)
    search = normalize_line_endings(old_string, newline)
    replacement = normalize_line_endings(new_string, newline)
    count = content.count(search)
    if count != expected_replacements:
        raise BlockEditError(
            f"Exact-match count mismatch: expected {expected_replacements}, found {count}; "
            "supply a more unique search string"
        )

    # Python str.replace(count) shares Desktop Commander's non-overlapping
    # exact block semantics; unlike fuzzy matching, it never picks a guess.
    updated = content.replace(search, replacement, expected_replacements)
    updated_bytes = updated.encode("utf-8")
    if len(updated_bytes) > max_bytes:
        raise BlockEditError("Edited file exceeds write limit")

    first = content.index(search)
    # A preview of the proposed content, not a second authorization signal.
    new_start = max(0, first - 100)
    new_end = min(len(updated), first + len(replacement) + 100)
    return {
        "updated": updated,
        "replacements": count,
        "preview": updated[new_start:new_end],
        "preview_truncated": new_start > 0 or new_end < len(updated),
        "new_size": len(updated_bytes),
        "newline_style": {"\r\n": "CRLF", "\n": "LF", "\r": "CR"}[newline],
    }
