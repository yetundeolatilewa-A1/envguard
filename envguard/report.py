"""Text and JSON output."""

from __future__ import annotations

import json


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


def format_text(report, *, quiet: bool = False) -> str:
    lines = []
    if not quiet:
        for f in report.findings:
            where = f"{f.file}:{f.line}" if f.line else f.file
            key = f"{f.key}: " if f.key else ""
            lines.append(f"{f.level:<7} {f.code}  {where}  {key}{f.message}")
    if report.ok:
        summary = "OK"
        if report.warnings:
            summary += f" with {_plural(report.warnings, 'warning')}"
    else:
        summary = f"FAILED: {_plural(report.errors, 'error')}"
        if report.warnings:
            summary += f", {_plural(report.warnings, 'warning')}"
    lines.append(summary)
    return "\n".join(lines)


def format_json(report) -> str:
    payload = {
        "ok": report.ok,
        "errors": report.errors,
        "warnings": report.warnings,
        "findings": [
            {
                "level": f.level,
                "code": f.code,
                "file": f.file,
                "line": f.line,
                "key": f.key,
                "message": f.message,
            }
            for f in report.findings
        ],
    }
    return json.dumps(payload, indent=2)
