from pathlib import Path

from .config import ConfigManager
from .display_curses import DisplayCurses
from .game import Game
from .high_scores import HighScoresManager
from .items import AllItems, ItemManager
from .player import Player

CONFIG_DIR: str = "config"
CONFIG_FILE: str = "vmclassic.toml"
HIGHSCORES_FILE: str = "highscores.toml"

ITEMS_DIR: str = "items"
SAVES_DIR: str = "saves"


def main() -> None:
    # Determine the directory that contains main.py
    working_dir = Path(__file__).resolve().parent

    # Load the configuration.
    config_manager = ConfigManager(working_dir, CONFIG_DIR, CONFIG_FILE)
    config = config_manager.load_configuration()

    # Load the high scores, and optionally display them and exit.
    high_scores_manager = HighScoresManager(working_dir, CONFIG_DIR, HIGHSCORES_FILE, config.max_scores)
    high_scores_manager.load_high_scores()
    if config.scores:
        high_scores_manager.display_high_scores()
        return

    config_manager.display_config(config)

    # Load the Items toml file which describes everything that exists in the game
    item_manager = ItemManager(working_dir, ITEMS_DIR, config.item_files)
    item_manager.load_item_definitions()
    all_items = AllItems(item_defs=item_manager.item_defs, items={}, called_names={})
    print(f"Loaded {len(item_manager.item_defs)} items from {len(config.item_files)} item files.\n")
    if config.verify or config.verify_summary:
        item_manager.verify_item_definitions(config.verify_summary)
        return
    if config.probabilities:
        item_manager.test_random_item_creation(trials=10000)
        return

    # See if there is a saved player, if not create a new one
    player_file = Path(working_dir / SAVES_DIR / f"{config.name}.toml")
    new_player = False
    if not player_file.exists():
        player = Player.create_new_player(config.name, all_items)
        new_player = True
    else:
        # TODO Else load the player from a saved toml file.
        player = Player.create_new_player(config.name, all_items)

    # Create a curses display and create the game engine
    display = DisplayCurses()
    game = Game(config, all_items, display, player)
    game.display_player_welcome(new_player)

    # Start the game playing
    display.run(game)

    # Save player
    # TODO Save the player as a toml file.


if __name__ == "__main__":
    main()
