# Roadmap

Rough priority order. Each item should become a GitHub issue.

## Checks
- [ ] Find unused variables: declared in the example but never read in the code (`os.environ`, `os.getenv`, `process.env`)
- [ ] Find undeclared variables: read in the code but missing from the example
- [ ] Warn when a secret-looking value (keys, tokens, private keys) appears in a file that is tracked by git
- [ ] More types: `uuid`, `email`, `path`, `duration`, `json`, `list`, and a `min=`/`max=` range for numbers
- [ ] Custom validators via a small plugin interface

## Usability
- [ ] Configuration in `pyproject.toml` (`[tool.envguard]`): default paths, strict mode, ignored variables
- [ ] Check several env files in one run (`.env`, `.env.local`, `.env.test`)
- [ ] `envguard diff` to compare two env files (for example staging and production) without printing values
- [ ] `envguard check --fix` to append missing variables with blank values
- [ ] GitHub Actions annotations output (`--format github`)
- [ ] Coloured terminal output

## Quality and release
- [ ] Property-based tests for the parser
- [ ] Compare parser behaviour with `python-dotenv` and Docker Compose on edge cases (multi-line values, `${VAR}` expansion)
- [ ] Support multi-line quoted values and variable interpolation
- [ ] Publish to PyPI (check name availability first) with trusted publishing
- [ ] Type hints throughout and `py.typed`
- [ ] Documentation site with recipes for Django, FastAPI, Docker Compose and GitHub Actions
