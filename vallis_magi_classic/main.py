from pathlib import Path

from .config.config import ConfigManager
from .config.high_scores import HighScoresManager
from .config.item_store import ItemStore
from .config.items import ItemManager
from .engine.display_curses import DisplayCurses
from .engine.game import Game
from .state.item_types import ItemKnowledge
from .state.player import Player
from .tools.localisation import initialise_localisation

CONFIG_FILE: str = "vmclassic.toml"
HIGHSCORES_FILE: str = "highscores.toml"
LANGUAGES_DIR: str = "languages"

ITEMS_DIR: str = "items"
SAVES_DIR: str = "saves"


def main() -> None:
    # Determine the directory that contains main.py
    working_dir = Path(__file__).resolve().parent

    # Load the configuration.
    config_manager = ConfigManager(working_dir, CONFIG_FILE)
    config_args = config_manager.get_configuration()
    config = config_manager.load_config(config_args.file, config_args.scores)

    initialise_localisation(config.terse, working_dir, LANGUAGES_DIR, config.language)

    # Load the high scores, and optionally display them and exit.
    high_scores_manager = HighScoresManager(working_dir, HIGHSCORES_FILE, config.max_scores)
    high_scores_manager.load_high_scores()
    if config.scores:
        high_scores_manager.display_high_scores()
        return

    # Load the Items toml file which describes everything that exists in the game
    item_manager = ItemManager(working_dir, ITEMS_DIR, config.item_files)
    item_manager.load_item_definitions()

    item_store = ItemStore(item_manager)
    item_knowledge = ItemKnowledge()

    # See if there is a saved player, if not create a new one
    player_file = Path(working_dir / SAVES_DIR / f"{config.name}.toml")
    if not player_file.exists():
        player = Player.create_new_player(config.name, item_store, item_knowledge)
    else:
        # TODO Else load the player from a saved toml file.
        player = Player.create_new_player(config.name, item_store, item_knowledge)

    # Create a curses display and create the game engine
    display = DisplayCurses()
    game = Game(config, item_manager, item_store, item_knowledge, display, player)

    # Start the game playing
    display.run(game)

    # Save player
    # TODO Save the player as a toml file.


if __name__ == "__main__":
    main()
