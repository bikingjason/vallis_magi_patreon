import argparse
from pathlib import Path

from .config_check import run_configuration_check
from .localise_check import run_localise_check


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(".."),
        help="Root directory containing Python source files.",
    )
    parser.add_argument(
        "--locales",
        type=str,
        help="Locale TOML files to check, comma separated.",
    )

    args = parser.parse_args()

    if Path("..") == args.source_root:
        working_dir = Path(__file__).resolve().parent.parent
    elif Path(".") == args.source_root:
        working_dir = Path(__file__).resolve().parent
    else:
        working_dir = Path(args.source_root)

    run_configuration_check(working_dir)

    locales = args.locales.split(",")
    run_localise_check(working_dir, locales)


if __name__ == "__main__":
    main()
