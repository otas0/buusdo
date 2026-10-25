"""Minimal Valve KeyValues (VDF) text parser for Steam manifests."""

from __future__ import annotations

from typing import Any


def parse_vdf(text: str) -> dict[str, Any]:
    """Parse a Steam-style VDF document into nested dicts.

    Values are strings. Duplicate keys under the same object become lists.
    """
    tokens = _tokenize(text)
    pos = 0

    def parse_value() -> Any:
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("Unexpected end of VDF")
        tok = tokens[pos]
        if tok == "{":
            pos += 1
            obj: dict[str, Any] = {}
            while pos < len(tokens) and tokens[pos] != "}":
                key = tokens[pos]
                pos += 1
                value = parse_value()
                if key in obj:
                    existing = obj[key]
                    if not isinstance(existing, list):
                        obj[key] = [existing, value]
                    else:
                        existing.append(value)
                else:
                    obj[key] = value
            if pos >= len(tokens) or tokens[pos] != "}":
                raise ValueError("Unclosed VDF object")
            pos += 1
            return obj
        pos += 1
        return tok

    root: dict[str, Any] = {}
    while pos < len(tokens):
        key = tokens[pos]
        pos += 1
        value = parse_value()
        root[key] = value
    return root


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        if ch in "{}":
            tokens.append(ch)
            i += 1
            continue
        if ch == '"':
            i += 1
            buf: list[str] = []
            while i < n:
                c = text[i]
                if c == "\\" and i + 1 < n:
                    buf.append(text[i + 1])
                    i += 2
                    continue
                if c == '"':
                    i += 1
                    break
                buf.append(c)
                i += 1
            tokens.append("".join(buf))
            continue
        # Unquoted token (rare in Steam files)
        start = i
        while i < n and text[i] not in ' \t\r\n{}"':
            i += 1
        tokens.append(text[start:i])
    return tokens
