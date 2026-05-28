from pathlib import Path

from .config import ConfigManager
from .game_state import GameState
from .high_scores import HighScoresManager
from .items import AllItems, DataManager

CONFIG_DIR: str = "config"
CONFIG_FILE: str = "vmclassic.toml"
HIGHSCORES_FILE: str = "highscores.toml"

DATA_DIR: str = "data"
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
    data_manager = DataManager(working_dir, DATA_DIR, config.data_files)
    item_defs = data_manager.load_data_definitions()
    all_items = AllItems(item_defs=item_defs, items={})
    print(f"Loaded {len(item_defs)} items from {len(config.data_files)} data files.\n")

    # Initialise the game state
    game_state = GameState(all_items)

    # See if there is a saved player, if not create a new one
    player_file = Path(working_dir / SAVES_DIR / f"{config.name}.toml")
    if not player_file.exists():
        game_state.create_new_player(config.name, all_items)
        game_state.player.display_player_welcome(game_state.all_items, True)
    # TODO Else load the player from a saved toml file.

    # Play Game

    # Save player
    # TODO Save the player as a toml file.


if __name__ == "__main__":
    main()
