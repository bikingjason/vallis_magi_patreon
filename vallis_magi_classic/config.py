import argparse
import tomllib
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .tools.localisation import _


@dataclass
class AppConfig:
    language: str = "en"
    terse: bool = False
    flush: bool = False
    jump: bool = False
    step: bool = False
    askme: bool = False
    showac: bool = False
    scores: bool = False
    debug: bool = False
    max_scores: int = 10

    name: str = ""
    fruit: str = ""
    file: str = "vmclassic.toml"

    item_files: dict[str, str] = field(default_factory=dict)


class ConfigManager:
    def __init__(self, working_dir: Path, config_dir: str, config_file_name: str) -> None:
        super().__init__()
        self.working_dir = working_dir
        self.file_path = Path(working_dir / config_dir / config_file_name)

        if self.file_path.suffix.lower() != ".toml":
            self.file_path = self.file_path.with_suffix(".toml")

    def build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Configure and run the application.")

        parser.add_argument("--scores", action="store_true", default=None, help="Show the high scores.")
        parser.add_argument("--file", default="vmclassic.toml", type=str, help="Save file name.")

        return parser

    def load_config(self, config_file: str, high_scores: bool) -> AppConfig:

        if not self.file_path.exists():
            print(f"\nConfig: {self.file_path} not found, using default config.\n")
            return AppConfig(file=config_file)

        with self.file_path.open("rb") as f:
            data = tomllib.load(f)

        config_section = data.get("config", {})
        data_files_section = data.get("data_files", {})

        if not isinstance(config_section, dict):
            config_section = {}

        if not isinstance(data_files_section, dict):
            data_files_section = {}

        valid_fields = {field.name for field in fields(AppConfig)}
        config_data = {key: value for key, value in config_section.items() if key in valid_fields}
        data_files = {str(key): str(value) for key, value in data_files_section.items()}

        config = AppConfig(
            language=config_data.get("language", "en").lower(),
            terse=config_data.get("terse", False),
            flush=config_data.get("flush", False),
            jump=config_data.get("jump", True),
            step=config_data.get("step", False),
            askme=config_data.get("askme", False),
            showac=config_data.get("showac", False),
            scores=high_scores,
            max_scores=config_data.get("max_scores", 10),
            name=config_data.get("name", ""),
            fruit=config_data.get("fruit", ""),
            file=config_file,
            item_files=data_files,
        )

        return config

    def get_configuration(self) -> argparse.Namespace:
        parser = self.build_parser()
        args = parser.parse_args()
        return args

    def display_config(self, config: AppConfig) -> None:
        output = asdict(config)

        app_config_str = _("Application configuration")
        print()
        print(app_config_str)
        print("-" * len(app_config_str))
        for key, value in output.items():
            if value is not None:
                print(f"{key}: {value}")
        print()
