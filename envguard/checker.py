"""Compare an env file with its example file."""

from __future__ import annotations

from dataclasses import dataclass, field

from .parser import parse
from .rules import parse_rule, validate

CODES = {
    "ENV001": "variable declared in the example is missing",
    "ENV002": "required variable is empty",
    "ENV003": "value has the wrong type or is not an allowed choice",
    "ENV004": "variable is not declared in the example",
    "ENV005": "variable is defined more than once",
    "ENV006": "bad envguard directive in the example",
    "ENV007": "line could not be parsed",
}


@dataclass
class Finding:
    level: str  # "error" or "warning"
    code: str
    file: str
    message: str
    line: object = None
    key: object = None


@dataclass
class Report:
    findings: list = field(default_factory=list)

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.level == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.level == "warning")

    @property
    def ok(self) -> bool:
        return self.errors == 0


def _last_wins(entries):
    mapping = {}
    for entry in entries:
        mapping[entry.key] = entry
    return mapping


def check(
    example_text: str,
    env_text: str,
    *,
    strict: bool = False,
    example_name: str = ".env.example",
    env_name: str = ".env",
    ignore=(),
) -> Report:
    """``ignore`` lists variable names that may exist in the env file without being declared."""
    ignored = set(ignore)
    findings = []

    def add(level, code, file, message, line=None, key=None):
        if strict and level == "warning":
            level = "error"
        findings.append(Finding(level, code, file, message, line, key))

    example = parse(example_text)
    env = parse(env_text)

    for name, parsed in ((example_name, example), (env_name, env)):
        for line, message in parsed.errors:
            add("error", "ENV007", name, message, line)
        seen = {}
        for entry in parsed.entries:
            if entry.key in seen:
                add(
                    "warning",
                    "ENV005",
                    name,
                    f"defined more than once (first at line {seen[entry.key]}); the last one wins",
                    entry.line,
                    entry.key,
                )
            else:
                seen[entry.key] = entry.line

    example_map = _last_wins(example.entries)
    env_map = _last_wins(env.entries)

    for key, entry in example_map.items():
        rule = parse_rule(entry.directives)
        for problem in rule.problems:
            add("error", "ENV006", example_name, problem, entry.line, key)
        actual = env_map.get(key)
        if actual is None:
            if rule.required:
                add(
                    "error",
                    "ENV001",
                    env_name,
                    f"missing (declared at {example_name}:{entry.line})",
                    None,
                    key,
                )
            continue
        if actual.value == "":
            if rule.required:
                add("error", "ENV002", env_name, "is empty but required", actual.line, key)
            continue
        problem = validate(actual.value, rule)
        if problem:
            add("error", "ENV003", env_name, problem, actual.line, key)

    for key, entry in env_map.items():
        if key not in example_map and key not in ignored:
            add("warning", "ENV004", env_name, f"not declared in {example_name}", entry.line, key)

    return Report(findings)
