import argparse
import tomllib
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from .high_scores import HighScore, load_high_scores


@dataclass
class AppConfig:
    terse: bool = False
    flush: bool = False
    jump: bool = False
    step: bool = False
    askme: bool = False
    showac: bool = False
    scores: bool = False
    name: str = ""
    fruit: str = ""
    file: str = "vmclassic.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure and run the application.")

    parser.add_argument("--scores", action="store_true", default=None, help="Show the high scores.")
    parser.add_argument("--file", default="vmclassic.toml", type=str, help="Save file name.")

    return parser


def config_path(file_name: str) -> Path:
    path = Path(file_name).expanduser()

    if not path.is_absolute():
        path = Path.cwd() / path

    if path.suffix.lower() != ".toml":
        path = path.with_suffix(".toml")

    return path


def load_config(args: argparse.Namespace) -> tuple[AppConfig, list[HighScore]]:
    path = config_path(args.file)

    if not path.exists():
        print(f"\nConfig: {path} not found, using default config.\n")
        return AppConfig(file=args.file), []

    with path.open("rb") as f:
        data = tomllib.load(f)

    config_section = data.get("config", {})
    high_scores_section = data.get("high_scores", [])
    high_scores = load_high_scores(high_scores_section)

    valid_fields = {field.name for field in fields(AppConfig)}
    config_data = {key: value for key, value in config_section.items() if key in valid_fields}

    config = AppConfig(
        terse=config_data.get("terse", False),
        flush=config_data.get("flush", False),
        jump=config_data.get("jump", True),
        step=config_data.get("step", False),
        askme=config_data.get("askme", False),
        showac=config_data.get("showac", False),
        scores=args.scores,
        name=config_data.get("name", ""),
        fruit=config_data.get("fruit", ""),
        file=args.file,
    )

    return config, high_scores


def get_arguments() -> tuple[AppConfig, list[HighScore]]:
    parser = build_parser()
    args = parser.parse_args()
    config, high_scores = load_config(args)

    return config, high_scores


def display_config(config: AppConfig) -> None:
    output = asdict(config)
    print("Application configuration")
    print("-------------------------")
    for key, value in output.items():
        if value is not None:
            print(f"{key}: {value}")
