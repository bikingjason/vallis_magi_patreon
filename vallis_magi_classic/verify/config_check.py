from dataclasses import asdict
from pathlib import Path

from ..config import ConfigManager
from ..high_scores import HighScoresManager
from ..items import ItemManager
from ..tools.localisation import initialise_localisation

# Note: I created copies here so that I am forced to check this
CONFIG_DIR: str = "config"
CONFIG_FILE: str = "vmclassic.toml"
HIGHSCORES_FILE: str = "highscores.toml"
LANGUAGES_DIR: str = "languages"

ITEMS_DIR: str = "items"
SAVES_DIR: str = "saves"


def run_configuration_check(working_dir: Path) -> None:

    # Load the configuration.
    config_manager = ConfigManager(working_dir, CONFIG_DIR, CONFIG_FILE)
    config = config_manager.load_config(CONFIG_FILE, True)

    initialise_localisation(config.terse, working_dir, LANGUAGES_DIR, config.language)

    # Load the high scores, and optionally display them and exit.
    high_scores_manager = HighScoresManager(working_dir, CONFIG_DIR, HIGHSCORES_FILE, config.max_scores)
    high_scores_manager.load_high_scores()
    high_scores_manager.display_high_scores()

    output = asdict(config)

    app_config_str = "Application configuration"
    print()
    print(app_config_str)
    print("-" * len(app_config_str))
    for key, value in output.items():
        if value is not None:
            print(f"{key}: {value}")
    print()

    # Load the Items toml file which describes everything that exists in the game
    item_manager = ItemManager(working_dir, ITEMS_DIR, config.item_files)
    item_manager.load_item_definitions()
    print(f"Loaded {len(item_manager.item_defs)} items from {len(config.item_files)} item files.\n")

    item_manager.verify_item_definitions(True)
    item_manager.verify_item_definitions(False)

    item_manager.test_random_item_creation(trials=10000)

    # See if there is a saved player, if not create a new one
    player_file = Path(working_dir / SAVES_DIR / f"{config.name}.toml")
    print()
    print("Checking for a saved player...")
    if not player_file.exists():
        print("No saved player found.")
    else:
        print(f"Saved player found: {config.name}.")
        # TODO game.display_player_welcome(new_player)
