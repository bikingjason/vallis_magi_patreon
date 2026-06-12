import tomllib
from pathlib import Path


class Localisation:
    def __init__(
        self,
        verbosity: str,
        working_dir: Path,
        languages_dir: str,
        language: str,
        default_language: str,
    ) -> None:
        self.working_dir = working_dir
        self.languages_dir = working_dir / languages_dir
        self.language = language
        self.default_language = default_language

        default_messages = self._load_language(verbosity, default_language)

        if self.language == default_language:
            configured_messages: dict[str, str] = {}
        else:
            configured_messages = self._load_language(verbosity, self.language)

        # English first, configured language second.
        # Configured language entries override English entries.
        self.messages: dict[str, str] = {
            **default_messages,
            **configured_messages,
        }

    def _load_language(self, verbosity: str, locale_language: str) -> dict[str, str]:

        if verbosity not in {"terse", "long"}:
            raise ValueError(f"Unknown translation verbosity: {verbosity!r}")

        path = self.languages_dir / f"{locale_language}.toml"

        if not path.exists():
            return {}

        with path.open("rb") as f:
            data = tomllib.load(f)

        common = data.get("common", {})
        selected = data.get(verbosity, {})

        if not isinstance(common, dict):
            raise TypeError(f"{path} [common] section is not a table")

        if not isinstance(selected, dict):
            raise TypeError(f"{path} [{verbosity}] section is not a table")

        # selected overrides common if a key appears in both
        translations = common | selected

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
    default_language: str = "en",
) -> None:
    global _localisation

    if terse:
        verbosity = "terse"
    else:
        verbosity = "long"

    _localisation = Localisation(verbosity, working_dir, languages_dir, language, default_language)


def _(original: str, **kwargs: object) -> str:
    if _localisation is None:
        return original.format(**kwargs) if kwargs else original

    return _localisation.text(original, **kwargs)
