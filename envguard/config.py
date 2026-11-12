"""Read defaults from ``[tool.envguard]`` in pyproject.toml."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None


class ConfigError(Exception):
    pass


OPTIONS = {
    "env": "a string (path of the env file)",
    "example": "a string (path of the example file)",
    "strict": "true or false",
    "ignore": "a list of variable names",
}


def _validate(table: dict, source: Path) -> dict:
    unknown = sorted(set(table) - set(OPTIONS))
    if unknown:
        raise ConfigError(
            f"unknown option(s) in [tool.envguard] of {source}: {', '.join(unknown)} "
            f"(allowed: {', '.join(OPTIONS)})"
        )
    for name in ("env", "example"):
        if name in table and not isinstance(table[name], str):
            raise ConfigError(f"[tool.envguard] {name} must be {OPTIONS[name]}")
    if "strict" in table and not isinstance(table["strict"], bool):
        raise ConfigError(f"[tool.envguard] strict must be {OPTIONS['strict']}")
    if "ignore" in table and not (
        isinstance(table["ignore"], list) and all(isinstance(i, str) for i in table["ignore"])
    ):
        raise ConfigError(f"[tool.envguard] ignore must be {OPTIONS['ignore']}")
    return table


def load_config(path=None) -> dict:
    """Return the ``[tool.envguard]`` table, or ``{}`` when there is none.

    With no ``path``, ``pyproject.toml`` in the current directory is used if it exists.
    An explicit ``path`` that does not exist is an error.
    """
    explicit = path is not None
    target = Path(path) if explicit else Path("pyproject.toml")
    if not target.is_file():
        if explicit:
            raise ConfigError(f"config file not found: {target}")
        return {}
    if tomllib is None:
        raise ConfigError("reading pyproject.toml on Python 3.10 needs the 'tomli' package (pip install tomli)")
    try:
        with target.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {target}: {exc}") from None
    except OSError as exc:
        raise ConfigError(f"cannot read {target}: {exc}") from None
    table = data.get("tool", {}).get("envguard", {})
    if not isinstance(table, dict):
        raise ConfigError(f"[tool.envguard] in {target} must be a table")
    return _validate(table, target)
