"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .checker import check
from .generate import generate
from .report import format_json, format_text


class CliError(Exception):
    pass


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise CliError(f"file not found: {path}") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise CliError(f"cannot read {path}: {exc}") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envguard", description="Validate .env files.")
    parser.add_argument("--version", action="version", version=f"envguard {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    check_p = sub.add_parser("check", help="check an env file against the example file")
    check_p.add_argument("--env", default=".env", help="env file to check (default: .env)")
    check_p.add_argument("--example", default=".env.example", help="example file (default: .env.example)")
    check_p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    check_p.add_argument("--format", choices=["text", "json"], default="text")
    check_p.add_argument("--quiet", action="store_true", help="only print the summary line")

    gen_p = sub.add_parser("generate", help="write a .env.example from a .env (values are not copied)")
    gen_p.add_argument("--env", default=".env")
    gen_p.add_argument("--output", default=".env.example", help="output file, or - for stdout")
    gen_p.add_argument("--force", action="store_true", help="overwrite the output file if it exists")
    return parser


def _run_check(args) -> int:
    report = check(
        _read(args.example),
        _read(args.env),
        strict=args.strict,
        example_name=args.example,
        env_name=args.env,
    )
    if args.format == "json":
        print(format_json(report))
    else:
        print(format_text(report, quiet=args.quiet))
    return 0 if report.ok else 1


def _run_generate(args) -> int:
    text, count = generate(_read(args.env))
    if args.output == "-":
        sys.stdout.write(text)
        return 0
    target = Path(args.output)
    if target.exists() and not args.force:
        raise CliError(f"{args.output} already exists (use --force to overwrite)")
    target.write_text(text, encoding="utf-8")
    plural = "" if count == 1 else "s"
    print(f"wrote {count} variable{plural} to {args.output}")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _run_check(args) if args.command == "check" else _run_generate(args)
    except CliError as exc:
        print(f"envguard: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
