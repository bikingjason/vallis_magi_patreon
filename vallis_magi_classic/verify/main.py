import argparse
from pathlib import Path

from .config_check import run_configuration_check
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

    # Determine the directory that contains main.py
    working_dir = Path(__file__).resolve().parent.parent

    run_configuration_check(working_dir)
    run_localise_check(args.source_root, args.locales)


if __name__ == "__main__":
    main()
