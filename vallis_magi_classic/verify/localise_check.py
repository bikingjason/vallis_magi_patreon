import ast
import re
import tomllib
from pathlib import Path

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


def load_toml(path: Path) -> dict[str, str]:
    with path.open("rb") as f:
        data = tomllib.load(f)

    result: dict[str, str] = {}

    for key, value in data.items():
        if not isinstance(value, str):
            raise TypeError(f"{path}: value for {key!r} is not a string")
        result[key] = value

    return result


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(text))


def check_locale(source_strings: set[str], locale_path: Path) -> bool:

    if locale_path.suffix.lower() != ".toml":
        locale_path = locale_path.with_suffix(".toml")

    locale = load_toml(locale_path)

    ok = True

    source_keys = set(source_strings)
    locale_keys = set(locale)

    missing = sorted(source_keys - locale_keys)
    extra = sorted(locale_keys - source_keys)

    if missing:
        ok = False
        print(f"\n{locale_path}: missing {len(missing)} strings")
        for key in missing:
            print(f"  MISSING: {key!r}")

    if extra:
        ok = False
        print(f"\n{locale_path}: extra {len(extra)} strings")
        for key in extra:
            print(f"  EXTRA: {key!r}")

    for key in sorted(source_keys & locale_keys):
        translated_value = locale[key]

        if translated_value == "":
            ok = False
            print(f"\n{locale_path}: empty translation")
            print(f"  KEY: {key!r}")

        if translated_value == key:
            ok = False
            print(f"\n{locale_path}: possibly untranslated")
            print(f"  KEY:   {key!r}")
            print(f"  VALUE: {translated_value!r}")

        source_placeholders = placeholders(key)
        translated_placeholders = placeholders(translated_value)

        if source_placeholders != translated_placeholders:
            ok = False
            print(f"\n{locale_path}: placeholder mismatch")
            print(f"  KEY:         {key!r}")
            print(f"  SOURCE:      {sorted(source_placeholders)}")
            print(f"  TRANSLATION: {sorted(translated_placeholders)}")
            print(f"  VALUE:       {translated_value!r}")

    return ok


def run_localise_check(source_root: Path, locales: list[str]) -> bool:
    source_strings = extract_source_strings(source_root)

    if not source_strings:
        print("No _(...) translation strings found.")
        return False

    print(f"Found {len(source_strings)} translation strings in source code.")

    all_ok = True

    for locale_path in locales:
        all_ok = check_locale(source_strings, locale_path) and all_ok

    if all_ok:
        print("\nAll locale files look complete.")
        return True

    return False
