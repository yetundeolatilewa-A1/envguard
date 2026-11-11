"""A small, strict-enough dotenv parser.

Supported: ``KEY=value``, ``export KEY=value``, single and double quotes (double
quotes understand ``\\n``, ``\\t``, ``\\"`` and ``\\\\``), blank lines, ``#`` comments and
inline comments (`` # ...`` after an unquoted value, or after a closing quote).

``# envguard: ...`` comments carry validation directives. A directive comment
applies to the next variable (a blank line in between discards it), or it can
follow the value on the same line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DIRECTIVE_LINE = re.compile(r"^#\s*envguard:\s*(.+)$")
_DIRECTIVE_INLINE = re.compile(r"^\s*envguard:\s*(.+)$")
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


@dataclass
class Entry:
    key: str
    value: str
    line: int
    directives: list = field(default_factory=list)


@dataclass
class ParseResult:
    entries: list = field(default_factory=list)
    errors: list = field(default_factory=list)  # (line number, message)


def _split_value(raw: str):
    """Return ``(value, inline_comment)`` for the text after ``=``."""
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        quote = raw[0]
        out = []
        i = 1
        while i < len(raw):
            char = raw[i]
            if quote == '"' and char == "\\" and i + 1 < len(raw):
                nxt = raw[i + 1]
                out.append(_ESCAPES.get(nxt, "\\" + nxt))
                i += 2
                continue
            if char == quote:
                rest = raw[i + 1 :].strip()
                if rest and not rest.startswith("#"):
                    raise ValueError("unexpected text after closing quote")
                return "".join(out), rest[1:].strip()
            out.append(char)
            i += 1
        raise ValueError("unterminated quote")
    if raw.startswith("#"):
        return "", raw[1:].strip()
    match = re.search(r"\s#", raw)
    if match:
        return raw[: match.start()].rstrip(), raw[match.end() :].strip()
    return raw, ""


def _tokens(text: str) -> list:
    return [t for t in re.split(r"[\s,]+", text.strip()) if t]


def parse(text: str) -> ParseResult:
    result = ParseResult()
    pending: list = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            pending = []
            continue
        if stripped.startswith("#"):
            match = _DIRECTIVE_LINE.match(stripped)
            if match:
                pending.extend(_tokens(match.group(1)))
            continue
        body = stripped
        if body.startswith("export ") or body.startswith("export\t"):
            body = body[7:].lstrip()
        if "=" not in body:
            result.errors.append((number, "expected KEY=VALUE"))
            pending = []
            continue
        key, _, raw_value = body.partition("=")
        key = key.strip()
        if not KEY_RE.match(key):
            result.errors.append((number, f"invalid variable name {key!r}"))
            pending = []
            continue
        try:
            value, comment = _split_value(raw_value)
        except ValueError as exc:
            result.errors.append((number, f"{key}: {exc}"))
            pending = []
            continue
        directives = list(pending)
        inline = _DIRECTIVE_INLINE.match(comment)
        if inline:
            directives.extend(_tokens(inline.group(1)))
        pending = []
        result.entries.append(Entry(key=key, value=value, line=number, directives=directives))
    return result
