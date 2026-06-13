import ast
import re
import tomllib
from pathlib import Path
from typing import Any

IGNORED_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}

PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")

VALID_VERBOSITIES = {"terse", "long"}


class TranslationStringExtractor(ast.NodeVisitor):
    def __init__(self, filename: Path) -> None:
        self.filename = filename
        self.strings: set[str] = set()

    @staticmethod
    def _is_translation_call(node: ast.Call) -> bool:
        # Matches _("text")
        if isinstance(node.func, ast.Name) and node.func.id == "_":
            return True

        # Matches localisation._("text") or something._("text")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "_":
            return True

        return False

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_translation_call(node):
            if node.args and isinstance(node.args[0], ast.Constant):
                value = node.args[0].value
                if isinstance(value, str):
                    self.strings.add(value)

        self.generic_visit(node)


def iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        files.append(path)

    return sorted(files)


def extract_strings_from_file(path: Path) -> set[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="utf-8-sig")

    tree = ast.parse(source, filename=str(path))
    extractor = TranslationStringExtractor(path)
    extractor.visit(tree)
    return extractor.strings


def extract_source_strings(root: Path) -> set[str]:
    strings: set[str] = set()

    for path in iter_python_files(root):
        strings.update(extract_strings_from_file(path))

    return strings


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(text))


def normalise_locale_path(languages_dir: Path, locale_name: str) -> Path:
    locale_path = languages_dir / locale_name

    if locale_path.suffix.lower() != ".toml":
        locale_path = locale_path.with_suffix(".toml")

    return locale_path


def load_raw_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Localisation file not found: {path}")

    with path.open("rb") as f:
        data = tomllib.load(f)

    return data


def require_table(path: Path, data: dict[str, Any], section_name: str) -> dict[str, Any]:
    section = data.get(section_name)

    if section is None:
        if section_name == "config":
            raise KeyError(f"{path}: missing required [config] section")
        return {}

    if not isinstance(section, dict):
        raise TypeError(f"{path}: [{section_name}] section is not a table")

    return section


def read_parent_language(path: Path, config: dict[str, Any]) -> str | None:
    if "parent" not in config:
        raise KeyError(f"{path}: [config] section must contain parent")

    parent = config["parent"]

    if not isinstance(parent, str):
        raise TypeError(f"{path}: [config].parent must be a string, got {type(parent).__name__}")

    parent = parent.strip()

    if parent == "":
        return None

    return parent


def validate_translation_section(
    path: Path,
    section_name: str,
    section: dict[str, Any],
) -> dict[str, str]:
    messages: dict[str, str] = {}

    for key, value in section.items():
        if not isinstance(value, str):
            raise TypeError(f"{path}: [{section_name}] value for {key!r} must be a string, got {type(value).__name__}")

        messages[key] = value

    return messages


def load_single_locale_sections(
    languages_dir: Path,
    locale_name: str,
) -> tuple[str | None, dict[str, str], dict[str, str], dict[str, str]]:
    path = normalise_locale_path(languages_dir, locale_name)
    data = load_raw_toml(path)

    config = require_table(path, data, "config")
    common_raw = require_table(path, data, "common")
    terse_raw = require_table(path, data, "terse")
    long_raw = require_table(path, data, "long")

    parent = read_parent_language(path, config)

    common = validate_translation_section(path, "common", common_raw)
    terse = validate_translation_section(path, "terse", terse_raw)
    long = validate_translation_section(path, "long", long_raw)

    return parent, common, terse, long


def load_effective_locale(
    languages_dir: Path,
    locale_name: str,
    verbosity: str,
    seen: list[str] | None = None,
) -> dict[str, str]:
    if verbosity not in VALID_VERBOSITIES:
        raise ValueError(f"Unknown translation verbosity: {verbosity!r}")

    if seen is None:
        seen = []

    if locale_name in seen:
        chain = " -> ".join([*seen, locale_name])
        raise ValueError(f"Circular localisation parent chain: {chain}")

    seen.append(locale_name)

    parent, common, terse, long = load_single_locale_sections(languages_dir, locale_name)

    selected = terse if verbosity == "terse" else long

    # Within a file, selected verbosity overrides common.
    local_messages = {
        **common,
        **selected,
    }

    if parent is None:
        return local_messages

    parent_messages = load_effective_locale(
        languages_dir=languages_dir,
        locale_name=parent,
        verbosity=verbosity,
        seen=seen,
    )

    # Parent first, locale second.
    # Locale entries override parent entries.
    return {
        **parent_messages,
        **local_messages,
    }


def load_local_file_keys(
    languages_dir: Path,
    locale_name: str,
) -> set[str]:
    """
    Returns keys physically present in this locale file's [common], [terse],
    and [long] sections. Parent files are not included here.
    """
    _parent, common, terse, long = load_single_locale_sections(languages_dir, locale_name)

    return set(common) | set(terse) | set(long)


def check_translation_values(
    source_strings: set[str],
    locale_path: Path,
    translations: dict[str, str],
    verbosity: str,
) -> bool:
    ok = True

    source_keys = set(source_strings)
    locale_keys = set(translations)

    missing = sorted(source_keys - locale_keys)
    extra = sorted(locale_keys - source_keys)

    if missing:
        ok = False
        print(f"\n{locale_path} [{verbosity}]: missing {len(missing)} strings")
        for key in missing:
            print(f"  MISSING: {key!r}")

    if extra:
        ok = False
        print(f"\n{locale_path} [{verbosity}]: extra {len(extra)} strings")
        for key in extra:
            print(f"  EXTRA: {key!r}")

    for key in sorted(source_keys & locale_keys):
        translated_value = translations[key]

        if translated_value == "":
            ok = False
            print(f"\n{locale_path} [{verbosity}]: empty translation")
            print(f"  KEY: {key!r}")

        if translated_value == key:
            ok = False
            print(f"\n{locale_path} [{verbosity}]: possibly untranslated")
            print(f"  KEY:   {key!r}")
            print(f"  VALUE: {translated_value!r}")

        source_placeholders = placeholders(key)
        translated_placeholders = placeholders(translated_value)

        if source_placeholders != translated_placeholders:
            ok = False
            print(f"\n{locale_path} [{verbosity}]: placeholder mismatch")
            print(f"  KEY:         {key!r}")
            print(f"  SOURCE:      {sorted(source_placeholders)}")
            print(f"  TRANSLATION: {sorted(translated_placeholders)}")
            print(f"  VALUE:       {translated_value!r}")

    return ok


def check_local_file_has_no_obsolete_keys(
    source_strings: set[str],
    languages_dir: Path,
    locale_name: str,
) -> bool:
    """
    Checks only the keys physically present in the requested locale file.

    This is useful because a child locale such as us.toml may contain only
    overrides, but any override it does contain should still refer to a real
    source string.
    """
    locale_path = normalise_locale_path(languages_dir, locale_name)
    local_keys = load_local_file_keys(languages_dir, locale_name)

    extra = sorted(local_keys - source_strings)

    if not extra:
        return True

    print(f"\n{locale_path}: obsolete/local extra {len(extra)} strings")
    for key in extra:
        print(f"  EXTRA: {key!r}")

    return False


def check_locale(
    source_strings: set[str],
    languages_dir: Path,
    locale_name: str,
) -> bool:
    locale_path = normalise_locale_path(languages_dir, locale_name)

    ok = True

    # Check that this specific file does not contain obsolete local overrides.
    ok = (
        check_local_file_has_no_obsolete_keys(
            source_strings=source_strings,
            languages_dir=languages_dir,
            locale_name=locale_name,
        )
        and ok
    )

    # Check effective merged translations for both verbosity modes:
    # parent chain + common + terse
    # parent chain + common + long
    for verbosity in ("terse", "long"):
        translations = load_effective_locale(
            languages_dir=languages_dir,
            locale_name=locale_name,
            verbosity=verbosity,
        )

        ok = (
            check_translation_values(
                source_strings=source_strings,
                locale_path=locale_path,
                translations=translations,
                verbosity=verbosity,
            )
            and ok
        )

    return ok


def run_localise_check(source_root: Path, locales: list[str]) -> bool:
    source_strings = extract_source_strings(source_root)

    if not source_strings:
        print("No _(...) translation strings found.")
        return False

    print(f"Found {len(source_strings)} translation strings in source code.")

    languages_dir = source_root / "languages"

    all_ok = True

    for locale_name in locales:
        all_ok = (
            check_locale(
                source_strings=source_strings,
                languages_dir=languages_dir,
                locale_name=locale_name,
            )
            and all_ok
        )

    if all_ok:
        print("\nAll locale files look complete.")
        return True

    return False
