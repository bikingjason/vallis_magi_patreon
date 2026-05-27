from pathlib import Path

from .config import display_config, get_configuration
from .game_state import GameState
from .high_scores import display_high_scores
from .items import AllItems, load_item_definitions


def main() -> None:
    # Determine the directory that contains main.py
    working_dir = Path(__file__).resolve().parent

    # Load the configuration. optionally display High Scores and exiting.
    config, high_scores = get_configuration(working_dir)

    if config.scores:
        display_high_scores(high_scores)
        return

    display_config(config)

    # Load the Items toml file which describes everything that exists in the game
    items_file = Path(working_dir / "data" / "items.toml")
    item_defs = load_item_definitions(items_file)
    all_items = AllItems(item_defs=item_defs, items={})
    print(f"Loaded {len(item_defs)} items from {items_file}\n")

    # Initialise the game state
    game_state = GameState(all_items)

    # See if there is a saved player, if not create a new one
    player_file = Path(working_dir / "saves" / f"{config.name}.toml")
    if not player_file.exists():
        game_state.create_new_player(config.name, all_items)
        game_state.player.display_player_welcome(game_state.all_items, True)
    # TODO Else load the player from a saved toml file.

    # Play Game

    # Save player
    # TODO Save the player as a toml file.


if __name__ == "__main__":
    main()
