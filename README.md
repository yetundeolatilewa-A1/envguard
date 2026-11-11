# envguard

Catch broken `.env` files before they break your app.

`envguard` compares an env file with your `.env.example` and tells you what's wrong: variables that are
**missing**, **empty**, **mistyped** (a port that isn't a number, a bad URL) or **undeclared**. It runs as a
command line tool in CI, in a pre-commit hook or by hand.

**Who it's for:** anyone who ships an app configured with environment variables and has lost time to a
missing key or a `DEBUG=maybe`. **Built with:** pure Python 3.9+, no dependencies.

## Install

```bash
pip install git+https://github.com/yetundeolatilewa-A1/envguard   # not on PyPI yet
```

## Quick start

Describe your variables in `.env.example`. Plain `KEY=` lines are required by default; add
`# envguard:` comments above a variable to add rules:

```dotenv
# envguard: url
DATABASE_URL=

# envguard: port
PORT=8000

# envguard: choices=dev|staging|prod
APP_ENV=dev

# envguard: optional url
SENTRY_DSN=
```

Then check a real env file:

```console
$ envguard check --env examples/bad.env --example examples/.env.example
error   ENV003  examples/bad.env:1  DATABASE_URL: expected a URL like scheme://host
error   ENV003  examples/bad.env:2  PORT: expected a port number (1-65535)
error   ENV003  examples/bad.env:3  DEBUG: expected a boolean (true/false/1/0/yes/no/on/off)
error   ENV003  examples/bad.env:4  APP_ENV: must be one of: dev, staging, prod
error   ENV001  examples/bad.env  REQUEST_TIMEOUT: missing (declared at examples/.env.example:16)
error   ENV002  examples/bad.env:5  SECRET_KEY: is empty but required
warning ENV004  examples/bad.env:6  LEGACY_FLAG: not declared in examples/.env.example
FAILED: 6 errors, 1 warning
```

Exit codes: `0` ok, `1` problems found, `2` usage error (for example a file is missing).

## Commands

| Command | What it does |
|---|---|
| `envguard check` | Compare `.env` with `.env.example`. Options: `--env`, `--example`, `--strict` (warnings fail too), `--format json`, `--quiet` |
| `envguard generate` | Write a `.env.example` from a `.env`. Values are **never copied**; it guesses types (`int`, `bool`, `url`...) from them. Options: `--env`, `--output` (`-` for stdout), `--force` |

## Directives

Put them in a comment directly above the variable (a blank line breaks the link), or after the value on
the same line: `DEBUG=false  # envguard: bool`. Combine several separated by spaces.

| Directive | Meaning |
|---|---|
| `required` | Must be present and non-empty (the default) |
| `optional` | May be missing or empty; if set, it is still type-checked |
| `int`, `float`, `bool`, `url`, `port` | Value must have this type |
| `choices=a\|b\|c` | Value must be one of these |

## Findings

| Code | Level | Meaning |
|---|---|---|
| ENV001 | error | Declared in the example, missing from the env file |
| ENV002 | error | Required variable is empty |
| ENV003 | error | Wrong type or not an allowed choice |
| ENV004 | warning | In the env file but not declared in the example |
| ENV005 | warning | Defined more than once (the last one wins) |
| ENV006 | error | Unknown or conflicting directive in the example |
| ENV007 | error | A line could not be parsed |

Error messages never print your values, so secrets don't end up in CI logs.

## Use in CI

```yaml
- run: pip install git+https://github.com/yetundeolatilewa-A1/envguard
- run: envguard check --env .env.ci --strict
```

## pre-commit

```yaml
repos:
  - repo: https://github.com/yetundeolatilewa-A1/envguard
    rev: main
    hooks:
      - id: envguard
        args: ["--env", ".env.ci"]   # a committed env file; real .env files should stay out of git
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m pytest
```

See [ROADMAP.md](ROADMAP.md) for planned work and [CONTRIBUTING.md](CONTRIBUTING.md) to help.

## License

MIT, see [LICENSE](LICENSE).
