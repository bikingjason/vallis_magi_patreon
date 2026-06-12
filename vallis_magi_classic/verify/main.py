import argparse
from pathlib import Path

from .localise_check import run_localise_check


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("."),
        help="Root directory containing Python source files",
    )
    parser.add_argument(
        "--locales",
        type=Path,
        nargs="+",
        help="Locale TOML files to check",
    )

    args = parser.parse_args()

    run_localise_check(args.locales)


if __name__ == "__main__":
    main()
