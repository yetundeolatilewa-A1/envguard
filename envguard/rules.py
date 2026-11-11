"""Directives (``# envguard: int optional ...``) and value validators."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

TYPES = ("int", "float", "bool", "url", "port")
_BOOLS = {"true", "false", "1", "0", "yes", "no", "on", "off"}
_INT = re.compile(r"[+-]?\d+")
_FLOAT = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


@dataclass
class Rule:
    required: bool = True
    type: object = None
    choices: object = None
    problems: list = field(default_factory=list)


def parse_rule(tokens) -> Rule:
    rule = Rule()
    for token in tokens:
        if token == "required":
            rule.required = True
        elif token == "optional":
            rule.required = False
        elif token in TYPES:
            if rule.type and rule.type != token:
                rule.problems.append(f"conflicting types {rule.type!r} and {token!r}")
            else:
                rule.type = token
        elif token.startswith("choices="):
            options = [o for o in token[len("choices=") :].split("|") if o]
            if options:
                rule.choices = options
            else:
                rule.problems.append("choices= needs at least one value, e.g. choices=dev|prod")
        else:
            rule.problems.append(f"unknown directive {token!r}")
    return rule


def _valid_url(value: str) -> bool:
    parts = urlsplit(value)
    if not parts.scheme:
        return False
    if parts.scheme in ("http", "https"):
        return bool(parts.netloc)
    return bool(parts.netloc or parts.path)


def validate(value: str, rule: Rule):
    """Return an error message, or ``None`` if the value is fine.

    Messages never contain the value itself, so secrets don't leak into CI logs.
    """
    if rule.choices is not None and value not in rule.choices:
        return "must be one of: " + ", ".join(rule.choices)
    kind = rule.type
    if kind == "int" and not _INT.fullmatch(value):
        return "expected an integer"
    if kind == "float" and not _FLOAT.fullmatch(value):
        return "expected a number"
    if kind == "bool" and value.lower() not in _BOOLS:
        return "expected a boolean (true/false/1/0/yes/no/on/off)"
    if kind == "url" and not _valid_url(value):
        return "expected a URL like scheme://host"
    if kind == "port" and not (_INT.fullmatch(value) and 1 <= int(value) <= 65535):
        return "expected a port number (1-65535)"
    return None
