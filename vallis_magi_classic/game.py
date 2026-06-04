from collections.abc import Callable
from dataclasses import dataclass

from .config import AppConfig
from .game_context import GameContext
from .game_types import CTRL_C, CTRL_R, ESCAPE, Direction
from .inventory import InventoryService
from .item_actions.armour import ArmourActions
from .item_actions.food import FoodActions
from .item_actions.inventory import InventoryActions
from .item_actions.potions import PotionActions
from .item_actions.rings import RingActions
from .item_actions.scrolls import ScrollActions
from .item_actions.wands import WandActions
from .item_actions.weapons import WeaponActions
from .items import AllItems, ItemInstanceId
from .player import Player
from .protocols.display_protocol import DisplayProtocol
from .protocols.game_protocol import GameProtocol

HELP_COMMANDS: list[tuple[str, str]] = [
    ("?", "Show this help message"),
    ("/", "Identify an object"),
    (">", "Go down a staircase"),
    ("s", "Search for a trap or secret door"),
    (".", "Rest for a while"),
    ("i", "Show inventory"),
    ("I", "Show a single inventory item"),
    ("q", "Quaff a potion"),
    ("r", "Read a scroll or paper"),
    ("e", "Eat food"),
    ("w", "Wield a weapon"),
    ("W", "Wear armour"),
    ("T", "Take armour off"),
    ("P", "Put on a ring"),
    ("R", "Remove a ring"),
    ("d", "Drop an object"),
    ("c", "Call or name an object"),
    (CTRL_R, "Repeat the last message"),
    ("Esc", "Cancel command"),
    ("S", "Save game"),
    ("Q", "Quit game"),
    ("z", "Zap a wand or staff"),
]


DIRECTIONS: dict[str, Direction] = {
    "h": (-1, 0),
    "j": (0, 1),
    "k": (0, -1),
    "l": (1, 0),
    "y": (-1, -1),
    "u": (1, -1),
    "b": (-1, 1),
    "n": (1, 1),
}


RUN_DIRECTIONS: dict[str, Direction] = {
    "H": (-1, 0),
    "J": (0, 1),
    "K": (0, -1),
    "L": (1, 0),
    "Y": (-1, -1),
    "U": (1, -1),
    "B": (-1, 1),
    "N": (1, 1),
}


GAME_TITLE = "Vallis Magi - curses prototype version 0.1"
GAME_HELP = "Press ? for help."

MAZE_HEIGHT = 24
MAZE_WIDTH = 70

LINE_TITLE = 0
LINE_START_OF_MAZE = 2
LINE_STATS = LINE_START_OF_MAZE + MAZE_HEIGHT
LINE_MESSAGE = LINE_STATS + 2


@dataclass
class PendingDirectionalCommand:
    command: str
    description: str
    handler: Callable[[Direction], None]


class Game(GameProtocol):
    def __init__(self, config: AppConfig, all_items: AllItems, display: DisplayProtocol, player: Player) -> None:
        self.config: AppConfig = config
        self.all_items: AllItems = all_items
        self.display: DisplayProtocol = display
        self.player: Player = player

        self.pending_directional_command: PendingDirectionalCommand | None = None
        self.last_message: str = ""
        self.should_quit: bool = False

        self.height: int = 0
        self.width: int = 0
        self.maze_height: int = MAZE_HEIGHT
        self.maze_width: int = MAZE_WIDTH

        self.inventory = InventoryService(
            config=self.config,
            display=self.display,
            all_items=self.all_items,
            player=self.player,
        )

        self.context = GameContext(
            config=self.config,
            display=self.display,
            all_items=self.all_items,
            inventory=self.inventory,
            player=self.player,
            redraw=self.draw_main_screen,
        )

        self.food_actions = FoodActions(self.context)

        self.armour_actions = ArmourActions(self.context)
        self.weapon_actions = WeaponActions(self.context)

        self.potion_actions = PotionActions(self.context)
        self.ring_actions = RingActions(self.context)
        self.scroll_actions = ScrollActions(self.context)
        self.wand_actions = WandActions(self.context)

        self.inventory_actions = InventoryActions(self.context)

        self.command_handlers: dict[str, Callable[[], bool]] = {
            "?": self.show_help,
            "/": self.identify_object,
            ">": self.go_down_stairs,
            "s": self.search,
            ".": self.rest,
            "i": self.show_inventory,
            "I": self.show_single_item_inventory,
            "q": self.potion_actions.quaff_potion,
            "r": self.scroll_actions.read_scroll,
            "e": self.food_actions.eat_food,
            "w": self.weapon_actions.wield_weapon,
            "W": self.armour_actions.wear_armour,
            "T": self.armour_actions.take_armour_off,
            "P": self.ring_actions.put_on_ring,
            "R": self.ring_actions.remove_ring,
            "d": self.inventory_actions.drop_object,
            "c": self.inventory_actions.call_object,
            CTRL_R: self.repeat_last_message,
            ESCAPE: self.cancel_command,
            "S": self.save_game,
            "Q": self.quit_game,
            "z": self.wand_actions.zap_wand,
        }

        self.directional_command_handlers: dict[str, PendingDirectionalCommand] = {
            "t": PendingDirectionalCommand(
                command="throw",
                description="throw something",
                handler=self.throw_item,
            ),
            "f": PendingDirectionalCommand(
                command="forward",
                description="forward until find something",
                handler=self.forward_until_find,
            ),
            "p": PendingDirectionalCommand(
                command="zap_direction",
                description="zap a wand in a direction",
                handler=self.zap_wand_in_direction,
            ),
        }

    def describe_item(self, item_id: ItemInstanceId | None) -> str:
        if item_id is None:
            return "nothing"

        item = self.all_items.items[item_id]
        definition = self.all_items.item_defs[item.definition_id]

        if item.quantity > 1:
            return f"{item.quantity} x {definition.name}"

        return definition.name

    def display_player_welcome(self, new_player: bool) -> None:

        player = self.player

        print(f"Welcome {'to' if new_player else 'back to'} the game, {player.name}!\n")
        print("Equipment")
        print("---------")
        print(f"Right hand: {self.describe_item(player.equipment.right_hand)}")
        print(f"Left hand:  {self.describe_item(player.equipment.left_hand)}")
        print(f"Body:       {self.describe_item(player.equipment.body)}")
        print(f"Head:       {self.describe_item(player.equipment.head)}")
        print()
        print("Backpack")
        print("--------")
        if not player.inventory.backpack:
            print("Empty")
        else:
            for item_id in player.inventory.backpack:
                print(f"- {self.describe_item(item_id)}")
        print()

    def run_game(self) -> None:

        self.height, self.width = self.display.getmaxyx()
        self.display.set_display_limits(self.width, self.height)
        self.display.set_message_line(LINE_MESSAGE)

        self.player.position = (0, 0)

        self.draw_main_screen()

        self.display.message(GAME_HELP)

        while not self.should_quit:
            key_text = self.display.getch()

            if key_text is None:
                continue

            if key_text == CTRL_C:
                break

            needs_redraw = self.handle_key(key_text)

            if needs_redraw:
                self.draw_main_screen()

    def draw_main_screen(self) -> None:

        self.display.clear()

        self.display.addstr(LINE_TITLE, 0, GAME_TITLE)
        self.display.addstr(LINE_START_OF_MAZE + self.player.position[1], self.player.position[0], "@")
        self.display.addstr(LINE_STATS, 0, "HP: 12/12   Level: 1   Gold: 0")
        self.display.addstr(LINE_MESSAGE, 0, self.last_message)

        self.display.refresh()

    def handle_key(self, key: str) -> bool:
        """
        Main key handler.

        `key` should be a single-character string, except special keys such as
        Escape and Ctrl keys, which should be passed as their control character.
        """

        if self.pending_directional_command is not None:
            self.handle_pending_direction(key)
            return True

        if key in DIRECTIONS:
            self.move(DIRECTIONS[key])
            return True

        if key in RUN_DIRECTIONS:
            self.run(RUN_DIRECTIONS[key])
            return True

        if key in self.directional_command_handlers:
            self.start_directional_command(self.directional_command_handlers[key])
            return True

        handler = self.command_handlers.get(key)

        if handler is not None:
            return handler()

        self.display.message(f"Unknown command: {key!r}")
        return False

    def handle_pending_direction(self, key: str) -> None:
        if key == ESCAPE:
            self.cancel_command()
            return

        direction = DIRECTIONS.get(key.lower())

        if direction is None:
            self.display.message("Direction expected.")
            return

        pending = self.pending_directional_command
        self.pending_directional_command = None

        if pending is None:
            return

        pending.handler(direction)

    def start_directional_command(self, command: PendingDirectionalCommand) -> None:
        self.pending_directional_command = command
        self.display.message(f"Direction for {command.description}?")

    # Movement

    def move(self, direction: Direction) -> None:
        dx, dy = direction

        new_x = self.player.position[0] + dx
        new_y = self.player.position[1] + dy

        if (new_x < 0) or (new_x >= self.maze_width) or (new_y < 0) or (new_y >= self.maze_height):
            return

        self.player.position = (new_x, new_y)

    def run(self, direction: Direction) -> None:
        dx, dy = direction
        self.display.message(f"Run by ({dx}, {dy}).")

    # Directional commands

    def throw_item(self, direction: Direction) -> None:
        dx, dy = direction
        self.display.message(f"Throw item by ({dx}, {dy}).")

    def forward_until_find(self, direction: Direction) -> None:
        dx, dy = direction
        self.display.message(f"Move forward until finding something by ({dx}, {dy}).")

    def zap_wand_in_direction(self, direction: Direction) -> None:
        dx, dy = direction
        self.display.message(f"Zap wand by ({dx}, {dy}).")

    # Immediate commands

    def show_help(self) -> bool:

        self.display.clear()

        lines = ["Commands:", ""]

        key_width = max(len(key) for key, _description in HELP_COMMANDS)

        for key, description in HELP_COMMANDS:
            lines.append(f"  {key:<{key_width}}  {description}")

        height, width = self.display.getmaxyx()

        for row, line in enumerate(lines[:height]):
            self.display.addstr(row, 0, line[: width - 1])

        self.display.refresh()
        self.display.getch()
        self.draw_main_screen()

        return False

    def identify_object(self) -> bool:
        self.display.message("Identify object.")
        return False

    def go_down_stairs(self) -> bool:
        self.display.message("Go down staircase.")
        return False

    def search(self) -> bool:
        self.display.message("Search for traps or secret doors.")
        return False

    def rest(self) -> bool:
        self.display.message("Rest for a while.")
        return False

    def show_inventory(self) -> bool:
        _, redraw = self.inventory.show_inventory()
        return redraw

    def show_single_item_inventory(self) -> bool:
        self.display.message("Show inventory for one item.")
        return False

    def repeat_last_message(self) -> bool:
        self.display.message(self.display.last_message)
        return False

    def cancel_command(self) -> bool:
        self.pending_directional_command = None
        self.display.message("Cancelled.")
        return False

    def save_game(self) -> bool:
        self.display.message("Save game.")
        return False

    def quit_game(self) -> bool:
        self.should_quit = True
        return False
