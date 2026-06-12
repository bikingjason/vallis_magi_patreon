import tomllib
from pathlib import Path
from typing import Any


class Localisation:
    def __init__(
        self,
        verbosity: str,
        working_dir: Path,
        languages_dir: str,
        language: str,
    ) -> None:
        self.working_dir = working_dir
        self.languages_dir = working_dir / languages_dir
        self.language = language

        if verbosity not in {"terse", "long"}:
            raise ValueError(f"Unknown translation verbosity: {verbosity!r}")

        self.messages: dict[str, str] = self._load_language(
            verbosity=verbosity,
            locale_language=language,
        )

    def _load_language(self, verbosity: str, locale_language: str) -> dict[str, str]:
        return self._load_language_chain(
            verbosity=verbosity,
            locale_language=locale_language,
            seen=[],
        )

    def _load_language_chain(
        self,
        verbosity: str,
        locale_language: str,
        seen: list[str],
    ) -> dict[str, str]:
        if locale_language in seen:
            chain = " -> ".join([*seen, locale_language])
            raise ValueError(f"Circular localisation parent chain: {chain}")

        seen.append(locale_language)

        messages, parent_language = self._load_single_language(
            verbosity=verbosity,
            locale_language=locale_language,
        )

        if parent_language is None:
            return messages

        parent_messages = self._load_language_chain(
            verbosity=verbosity,
            locale_language=parent_language,
            seen=seen,
        )

        # Parent first, locale second.
        # Locale entries override parent entries.
        return {
            **parent_messages,
            **messages,
        }

    def _load_single_language(
        self,
        verbosity: str,
        locale_language: str,
    ) -> tuple[dict[str, str], str | None]:
        path = self.languages_dir / f"{locale_language}.toml"

        if not path.exists():
            raise FileNotFoundError(f"Localisation file not found: {path}")

        with path.open("rb") as f:
            data = tomllib.load(f)

        config = data.get("config")
        common = data.get("common", {})
        selected = data.get(verbosity, {})

        if not isinstance(config, dict):
            raise TypeError(f"{path} must contain a [config] table")

        if "parent" not in config:
            raise KeyError(f"{path} [config] table must contain parent")

        if not isinstance(common, dict):
            raise TypeError(f"{path} [common] section is not a table")

        if not isinstance(selected, dict):
            raise TypeError(f"{path} [{verbosity}] section is not a table")

        parent_language = self._read_parent_language(path, config)

        # selected overrides common if a key appears in both.
        translations = {
            **common,
            **selected,
        }

        messages = self._validate_messages(path, translations)

        return messages, parent_language

    @staticmethod
    def _read_parent_language(path: Path, config: dict[str, Any]) -> str | None:
        parent_language = config["parent"]

        if not isinstance(parent_language, str):
            raise TypeError(f"{path} [config] parent must be a string, got {type(parent_language).__name__}")

        parent_language = parent_language.strip()

        if parent_language == "":
            return None

        return parent_language

    @staticmethod
    def _validate_messages(path: Path, translations: dict[str, Any]) -> dict[str, str]:
        messages: dict[str, str] = {}

        for key, value in translations.items():
            if isinstance(value, str):
                messages[key] = value
            else:
                raise ValueError(f"Invalid localisation entry in {path}: {key!r} must have a string value, got {type(value).__name__}")

        return messages

    def text(self, original: str, **kwargs: object) -> str:
        template = self.messages.get(original, original)

        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError:
                return template

        return template


_localisation: Localisation | None = None


def initialise_localisation(
    terse: bool,
    working_dir: Path,
    languages_dir: str,
    language: str,
) -> None:
    global _localisation

    if terse:
        verbosity = "terse"
    else:
        verbosity = "long"

    _localisation = Localisation(
        verbosity=verbosity,
        working_dir=working_dir,
        languages_dir=languages_dir,
        language=language,
    )


def _(original: str, **kwargs: object) -> str:
    if _localisation is None:
        return original.format(**kwargs) if kwargs else original

    return _localisation.text(original, **kwargs)
