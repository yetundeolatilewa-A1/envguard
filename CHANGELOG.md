# Changelog

## 0.1.0 (unreleased)
- `envguard check`: missing, empty, mistyped and undeclared variables, text and JSON output, `--strict`.
- `envguard generate`: create a `.env.example` from a `.env` without copying values.
- Directives: `required`, `optional`, `int`, `float`, `bool`, `url`, `port`, `choices=`.
- pre-commit hook.
- New types `uuid` and `email` (also detected by `generate`).
- Configuration via `[tool.envguard]` in pyproject.toml (`env`, `example`, `strict`, `ignore`), `--config` and `--ignore` options.
- `envguard scan`: find variables read in Python/JS/TS code that are missing from the example (`ENV101`), and with `--unused` the reverse (`ENV102`).
