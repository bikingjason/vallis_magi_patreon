from collections.abc import Callable
from dataclasses import dataclass

from .config import AppConfig
from .game_types import CTRL_C, CTRL_R, ESCAPE, Direction
from .items import AllItems, ItemDefId, ItemDefinition, ItemInstance, ItemInstanceId
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
    ("o", "Examine or set options"),
    (CTRL_R, "Repeat the last message"),
    ("Esc", "Cancel command"),
    ("v", "Print program version number"),
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


GAME_TITLE = "Vallis Magi - curses prototype"
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
    def __init__(self, config: AppConfig, all_items: AllItems, display: DisplayProtocol) -> None:
        self.config: AppConfig = config
        self.all_items: AllItems = all_items
        self.display: DisplayProtocol = display
        self._player: Player | None = None

        self.pending_directional_command: PendingDirectionalCommand | None = None
        self.last_message: str = ""
        self.should_quit: bool = False

        self.height: int = 0
        self.width: int = 0
        self.maze_height: int = MAZE_HEIGHT
        self.maze_width: int = MAZE_WIDTH

        self.command_handlers: dict[str, Callable[[], bool]] = {
            "?": self.show_help,
            "/": self.identify_object,
            ">": self.go_down_stairs,
            "s": self.search,
            ".": self.rest,
            "i": self.show_inventory,
            "I": self.show_single_item_inventory,
            "q": self.quaff_potion,
            "r": self.read_scroll,
            "e": self.eat_food,
            "w": self.wield_weapon,
            "W": self.wear_armour,
            "T": self.take_armour_off,
            "P": self.put_on_ring,
            "R": self.remove_ring,
            "d": self.drop_object,
            "c": self.call_object,
            "o": self.examine_options,
            CTRL_R: self.repeat_last_message,
            ESCAPE: self.cancel_command,
            "v": self.print_version,
            "S": self.save_game,
            "Q": self.quit_game,
            "z": self.zap_wand_or_staff,
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

    @property
    def player(self) -> Player:
        if self._player is None:
            raise RuntimeError("Player has not yet been created. Call Game.create_new_player() first.")

        return self._player

    def create_new_player(self, name: str) -> None:

        all_items = self.all_items

        food = all_items.new_item(ItemDefId("food"), 2)
        ring_mail = all_items.new_item(ItemDefId("ring_mail"))
        long_sword = all_items.new_item(ItemDefId("long_sword"))

        ring_of_slow_digestion = all_items.new_item(ItemDefId("ring_of_slow_digestion"))
        potion_of_quench_thirst = all_items.new_item(ItemDefId("potion_of_quench_thirst"))
        scroll_genocide = all_items.new_item(ItemDefId("scroll_genocide"))
        wand_cold = all_items.new_item(ItemDefId("wand_cold"))
        scale_mail = all_items.new_item(ItemDefId("scale_mail"))
        bow = all_items.new_item(ItemDefId("bow"))

        player = Player(name, self.display)

        player.inventory.backpack.append(food)
        player.inventory.backpack.append(ring_of_slow_digestion)
        player.inventory.backpack.append(potion_of_quench_thirst)
        player.inventory.backpack.append(scroll_genocide)
        player.inventory.backpack.append(wand_cold)
        player.inventory.backpack.append(scale_mail)
        player.inventory.backpack.append(bow)
        player.equipment.body = ring_mail
        player.equipment.right_hand = long_sword

        self._player = player

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

    def item_matches_type(
        self,
        item_def: ItemDefinition,
        item_type: str,
    ) -> bool:
        """
        Return True if this item definition belongs to the requested inventory group.
        """

        match item_type:
            case "armour":
                return item_def.is_armour

            case "food":
                return item_def.is_food

            case "potion":
                return item_def.is_potion

            case "ring":
                return item_def.is_ring

            case "scroll":
                return item_def.is_scroll

            case "wand":
                return item_def.is_wand

            case "weapon":
                return item_def.is_weapon

            case "callable":
                return item_def.is_scroll or item_def.is_potion or item_def.is_ring or item_def.is_wand

            case _:
                raise ValueError(f"Unknown item type: {item_type!r}")

    def inventory_name(
        self,
        item: ItemInstance,
        item_def: ItemDefinition,
    ) -> str:
        """
        Return the display name for an inventory item.

        This is the equivalent of Rogue's inv_name(obj, FALSE).
        You can expand this later for identified/cursed/charges/etc.
        """

        if item.quantity > 1:
            return f"{item.quantity} {item_def.name}s"

        return item_def.name

    def show_inventory_window(
        self,
        lines: list[str],
    ) -> None:
        """
        Display a multi-line inventory list.

        Replace this with your curses/window implementation later.
        """

        self.display.clear()

        height, width = self.display.getmaxyx()

        for row, line in enumerate(lines[:height]):
            self.display.addstr(row, 0, line[: width - 1])

        self.display.refresh()
        self.display.message("--Press space to continue--")
        self.display.getch()
        self.draw_main_screen()

    def _show_inventory(
        self,
        item_ids: list[ItemInstanceId] | None = None,
        item_type: str | None = None,
    ) -> bool:
        """
        Show inventory contents.

        This is the Python equivalent of Rogue's inventory(list, type).

        `item_ids` is the list of item instance ids to display.
        If omitted, the player's pack is used.

        `item_type` can be used to filter by item group, for example:
            "armour"
            "food"
            "potion"
            "ring"
            "scroll"
            "wand"
            "weapon"
            "callable"

        Returns True if at least one item was shown, otherwise False.
        """

        player = self.player

        if item_ids is None:
            item_ids = player.inventory.backpack

        lines: list[str] = []

        for index, item_id in enumerate(item_ids):
            item = self.all_items.items[item_id]
            item_def = self.all_items.item_defs[item.definition_id]

            if item_type is not None and not self.item_matches_type(item_def, item_type):
                continue

            letter = chr(ord("a") + index)
            lines.append(f"{letter}) {self.inventory_name(item, item_def)}")

        if not lines:
            if self.config.terse:
                self.display.message("Empty handed." if item_type is None else "Nothing appropriate.")
            else:
                self.display.message("You are empty handed." if item_type is None else "You don't have anything appropriate.")
            return False

        if len(lines) == 1:
            self.display.message(lines[0])
            return True

        # TODO - Do I need the slow_inventory option?
        # if self.config.slow_invent:
        #     for line in lines:
        #         self.display.message(line)
        # else:
        #     self.show_inventory_window(lines)

        self.show_inventory_window(lines)

        return True

    def pick_item(
        self,
        purpose: str,
        item_type: str | None = None,
    ) -> ItemInstanceId | None:
        """
        Ask the player to choose an item from their inventory.

        `purpose` is the verb phrase shown to the player, for example:
            "read"
            "quaff"
            "drop"
            "wear"

        `item_type` can later be used to filter by ISA_GROUPS.
        For now it is accepted but not used.

        Returns the selected ItemInstanceId, or None if the player cancels.
        """

        player = self.player

        if not player.inventory.backpack:
            self.display.message("You aren't carrying anything.")
            return None

        while True:
            if not self.config.terse:
                prompt = f"Which object do you want to {purpose}? (* for list): "
            else:
                prompt = f"{purpose} what? (* for list): "
            self.display.message(prompt)

            ch = self.display.getch()
            self.display.message("")

            # Give the player a chance to abort the command.
            if not ch or (ch in ("\x1b", "\x07")):  # ESCAPE or Ctrl-G
                self.after = False
                self.display.message("")
                return None

            if ch == "*":
                # TODO - Implement item_type filtering. Do I need both? Probably...
                shown_any = self._show_inventory()  # item_type)

                if not shown_any:
                    self.after = False
                    return None

                continue

            index = ord(ch) - ord("a")

            if index < 0 or index >= len(player.inventory.backpack):
                last_letter = chr(ord("a") + len(player.inventory.backpack) - 1)
                self.display.message(f"Please specify a letter between 'a' and '{last_letter}'")
                continue

            return player.inventory.backpack[index]

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

    def zap_wand_or_staff(self) -> bool:
        self.display.message("Zap a wand or staff.")
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
        self._show_inventory()
        return False

    def show_single_item_inventory(self) -> bool:
        self.display.message("Show inventory for one item.")
        return False

    def quaff_potion(self) -> bool:
        self.display.message("Quaff potion.")
        return False

    def read_scroll(self) -> bool:
        self.display.message("Read paper.")
        return False

    def eat_food(self) -> bool:
        self.display.message("Eat food.")
        return False

    def wield_weapon(self) -> bool:
        self.display.message("Wield weapon.")
        return False

    def wear_armour(self) -> bool:
        self.display.message("Wear armour.")
        return False

    def take_armour_off(self) -> bool:
        self.display.message("Take armour off.")
        return False

    def put_on_ring(self) -> bool:
        self.display.message("Put on ring.")
        return False

    def remove_ring(self) -> bool:
        self.display.message("Remove ring.")
        return False

    def drop_object(self) -> bool:
        self.display.message("Drop object.")
        return False

    def call_object(self) -> bool:
        self.display.message("Call object.")
        return False

    def examine_options(self) -> bool:
        self.display.message("Examine or set options.")
        return False

    def repeat_last_message(self) -> bool:
        self.display.message(self.display.last_message)
        return False

    def cancel_command(self) -> bool:
        self.pending_directional_command = None
        self.display.message("Cancelled.")
        return False

    def print_version(self) -> bool:
        self.display.message("Vallis Magi Rogue prototype version 0.1.")
        return False

    def save_game(self) -> bool:
        self.display.message("Save game.")
        return False

    def quit_game(self) -> bool:
        self.should_quit = True
        return False
