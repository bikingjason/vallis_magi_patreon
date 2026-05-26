import argparse
import tomllib
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import tomli_w


@dataclass
class AppConfig:
    terse: bool = False
    flush: bool = False
    jump: bool = False
    step: bool = False
    askme: bool = False
    showac: bool = False
    name: str = ""
    fruit: str = ""
    file: str = "vmclassic.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure and run the application.")

    parser.add_argument("--terse", action="store_true", default=None, help="Terse output.")
    parser.add_argument("--flush", action="store_true", default=None, help="Flush typeahead during battle.")
    parser.add_argument("--jump", action="store_false", default=True, help="Show position only at end of run.")
    parser.add_argument("--step", action="store_true", default=None, help="Do inventories one line at a time.")
    parser.add_argument("--askme", action="store_true", default=None, help="Ask me about unidentified things.")
    parser.add_argument("--showac", action="store_true", default=None, help="Show armour class instead of protection.")

    parser.add_argument("--name", default=None, type=str, help="User's name.")
    parser.add_argument("--fruit", default=None, type=str, help="Name of favourite fruit.")
    parser.add_argument("--file", default="vmclassic.toml", type=str, help="Save file name.")

    return parser


def config_path(file_name: str) -> Path:
    path = Path(file_name).expanduser()

    if not path.is_absolute():
        path = Path.cwd() / path

    if path.suffix.lower() != ".toml":
        path = path.with_suffix(".toml")

    return path


def load_config(file_name: str) -> AppConfig:
    path = config_path(file_name)

    if not path.exists():
        return AppConfig(file=file_name)

    with path.open("rb") as f:
        data = tomllib.load(f)

    config_section = data.get("config", {})

    valid_fields = {field.name for field in fields(AppConfig)}
    config_data = {key: value for key, value in config_section.items() if key in valid_fields}

    return AppConfig(
        terse=config_data.get("terse", False),
        flush=config_data.get("flush", False),
        jump=config_data.get("jump", True),
        step=config_data.get("step", False),
        askme=config_data.get("askme", False),
        showac=config_data.get("showac", False),
        name=config_data.get("name", ""),
        fruit=config_data.get("fruit", ""),
        file=file_name,
    )


def apply_args(config: AppConfig, args: argparse.Namespace) -> AppConfig:
    for key in ("terse", "flush", "jump", "step", "askme", "showac"):
        value = getattr(args, key)
        if value is not None:
            setattr(config, key, value)

    if args.name is not None:
        config.name = args.name.strip()

    if args.fruit is not None:
        config.fruit = args.fruit.strip()

    config.file = args.file
    return config


def get_arguments() -> AppConfig:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.file)
    config = apply_args(config, args)
    return config


def display_config(config: AppConfig) -> None:
    output = asdict(config)
    print("Application configuration")
    print("-------------------------")
    for key, value in output.items():
        print(f"{key}: {value}")


def save_config(config: AppConfig) -> None:
    if not config.file:
        return

    save_path = config_path(config.file)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    config_data = {
        "config": asdict(config),
    }

    with save_path.open("wb") as f:
        tomli_w.dump(config_data, f)

    display_config(config)
