"""Command-line interface for odiatranslit.

Examples:
    odiatranslit "ଓଡ଼ିଆ"                    # -> ōṛiā
    odiatranslit "ନମସ୍କାର" -s Hunterian      # -> namaskara
    odiatranslit -r "namaskAra" -s ITRANS   # -> ନମସ୍କାର
    odiatranslit -i input.txt -o output.txt
    echo "ଜଗନ୍ନାଥ" | odiatranslit
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._engine import SCHEMES
from .api import from_roman, to_roman


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odiatranslit",
        description="Transliterate Odia text to Roman script and back.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="text to convert (reads from --input or stdin if omitted)",
    )
    parser.add_argument(
        "-s",
        "--scheme",
        choices=SCHEMES,
        default="ISO15919",
        help="romanisation scheme (default: %(default)s)",
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="convert Roman -> Odia instead of Odia -> Roman",
    )
    parser.add_argument(
        "--reversible",
        action="store_true",
        help="escape output so it converts back exactly (ISO15919 / ITRANS)",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="read text from this file (UTF-8)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="write the result to this file instead of stdout",
    )
    return parser


def _read_text(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    if args.text is not None and args.input is not None:
        parser.error("give either TEXT or --input, not both")

    if args.text is not None:
        return str(args.text)
    if args.input is not None:
        try:
            return str(args.input.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            parser.error(f"cannot read {args.input}: {exc}")
    if sys.stdin.isatty():
        parser.error("no input given; pass TEXT, --input FILE, or pipe text in")

    return sys.stdin.read()


def _convert(text: str, args: argparse.Namespace) -> str:
    if args.reverse:
        return from_roman(text, args.scheme)
    return to_roman(text, args.scheme, reversible=args.reversible)


def _ensure_utf8_stdout() -> None:
    # Windows consoles often default to cp1252, which can't print Odia.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.reverse and args.reversible:
        parser.error("--reversible only applies to Odia -> Roman")
    if args.reversible and args.scheme == "Hunterian":
        print("note: Hunterian is lossy; --reversible has no effect", file=sys.stderr)

    result = _convert(_read_text(args, parser), args)

    if args.output is not None:
        try:
            args.output.write_text(result, encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            parser.error(f"cannot write {args.output}: {exc}")
    else:
        _ensure_utf8_stdout()
        # Text from files/stdin usually ends with a newline already.
        if result:
            print(result, end="" if result.endswith("\n") else "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
