"""Find environment variables read by your code and compare them with the example file.

This is a static scan of string literals. It recognises:

* Python: ``os.environ["X"]``, ``os.environ.get("X")``, ``os.environ.setdefault("X", ...)``,
  ``os.getenv("X")`` (and the same calls imported without ``os.``)
* JavaScript / TypeScript: ``process.env.X``, ``process.env["X"]``, ``import.meta.env.X``

Names built at run time (``os.environ[name]``) are not detected, and commented-out
lines are skipped only when the whole line is a comment.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .checker import Finding, Report
from .parser import parse

SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
    ".tox", ".mypy_cache", ".pytest_cache", "site-packages", ".eggs",
}
# Set by the operating system or shell rather than by your application's configuration.
SYSTEM_VARS = {
    "PATH", "HOME", "USER", "USERNAME", "PWD", "SHELL", "LANG", "TERM", "TMPDIR", "TEMP", "TMP",
    "VIRTUAL_ENV",
}
MAX_FILE_BYTES = 1_000_000

_NAME = r"[A-Za-z_][A-Za-z0-9_]*"
_PATTERNS = [
    re.compile(rf"""\benviron\s*\[\s*['"]({_NAME})['"]\s*\]"""),
    re.compile(rf"""\b(?:environ\.get|environ\.setdefault|getenv)\s*\(\s*['"]({_NAME})['"]"""),
    re.compile(rf"""\bprocess\.env\.({_NAME})\b"""),
    re.compile(rf"""\bprocess\.env\s*\[\s*['"]({_NAME})['"]\s*\]"""),
    re.compile(rf"""\bimport\.meta\.env\.({_NAME})\b"""),
]


@dataclass
class Usage:
    file: str
    line: int


def _is_comment(stripped: str, suffix: str) -> bool:
    if suffix == ".py":
        return stripped.startswith("#")
    return stripped.startswith(("//", "*", "/*"))


def iter_source_files(paths):
    """Yield source files under ``paths`` (files are taken as given, directories are walked)."""
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            raise FileNotFoundError(raw)
        if path.is_file():
            yield path
            continue
        for root, dirs, files in os.walk(path):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info"))
            for name in sorted(files):
                if Path(name).suffix in SOURCE_SUFFIXES:
                    yield Path(root) / name


def find_usages(paths):
    """Return ``(usages, files_scanned)``; ``usages`` maps a variable name to its first use."""
    usages = {}
    scanned = 0
    for path in iter_source_files(paths):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        for number, line in enumerate(text.splitlines(), start=1):
            if _is_comment(line.strip(), path.suffix):
                continue
            for pattern in _PATTERNS:
                for match in pattern.finditer(line):
                    usages.setdefault(match.group(1), Usage(path.as_posix(), number))
    return usages, scanned


def scan(
    example_text: str,
    usages: dict,
    *,
    unused: bool = False,
    ignore=(),
    strict: bool = False,
    example_name: str = ".env.example",
) -> Report:
    """Compare variables used in code with those declared in the example file."""
    findings = []

    def add(level, code, file, message, line=None, key=None):
        if strict and level == "warning":
            level = "error"
        findings.append(Finding(level, code, file, message, line, key))

    parsed = parse(example_text)
    for line, message in parsed.errors:
        add("error", "ENV007", example_name, message, line)
    declared = {entry.key: entry for entry in parsed.entries}
    ignored = set(ignore)

    for name, usage in usages.items():
        if name in declared or name in ignored or name in SYSTEM_VARS:
            continue
        add("warning", "ENV101", usage.file, f"used in code but not declared in {example_name}", usage.line, name)

    if unused:
        for key, entry in declared.items():
            if key not in usages and key not in ignored:
                add("warning", "ENV102", example_name, "declared but never read in the scanned code", entry.line, key)
    return Report(findings)
