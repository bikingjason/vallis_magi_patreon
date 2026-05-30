import curses
from collections.abc import Callable
from dataclasses import dataclass

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
    ("l", "Repeat the last message"),
    ("Esc", "Cancel command"),
    ("v", "Print program version number"),
    ("S", "Save game"),
    ("Q", "Quit game"),
    ("z", "Zap a wand or staff"),
]

Direction = tuple[int, int]


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


ESCAPE = "\x1b"


@dataclass
class PendingDirectionalCommand:
    command: str
    description: str
    handler: Callable[[Direction], None]


class Game:
    def __init__(self) -> None:
        self.pending_directional_command: PendingDirectionalCommand | None = None
        self.last_message: str = ""
        self.screen: curses.window | None = None
        self.should_quit = False

        self.command_handlers: dict[str, Callable[[], None]] = {
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
            "l": self.repeat_last_message,
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

    def set_screen(self, screen: curses.window) -> None:
        self.screen = screen

    def draw_main_screen(self) -> None:
        if self.screen is None:
            return

        self.screen.clear()

        self.screen.addstr(0, 0, "Vallis Magi - curses prototype")
        self.screen.addstr(2, 0, "Press ? for help.")
        self.screen.addstr(4, 0, "@")
        self.screen.addstr(22, 0, "HP: 12/12   Level: 1   Gold: 0")
        self.screen.addstr(23, 0, self.last_message)

        self.screen.refresh()

    def message(self, text: str) -> None:
        self.last_message = text

        if self.screen is None:
            print(text)
            return

        height, width = self.screen.getmaxyx()
        row = height - 1

        self.screen.move(row, 0)
        self.screen.clrtoeol()
        self.screen.addstr(row, 0, text[: width - 1])
        self.screen.refresh()

    def handle_key(self, key: str) -> None:
        """
        Main key handler.

        `key` should be a single-character string, except special keys such as
        Escape and Ctrl keys, which should be passed as their control character.
        """

        if self.pending_directional_command is not None:
            self.handle_pending_direction(key)
            return

        if key in DIRECTIONS:
            self.move(DIRECTIONS[key])
            return

        if key in RUN_DIRECTIONS:
            self.run(RUN_DIRECTIONS[key])
            return

        if key in self.directional_command_handlers:
            self.start_directional_command(self.directional_command_handlers[key])
            return

        handler = self.command_handlers.get(key)

        if handler is not None:
            handler()
            return

        self.message(f"Unknown command: {key!r}")

    def handle_pending_direction(self, key: str) -> None:
        if key == ESCAPE:
            self.cancel_command()
            return

        direction = DIRECTIONS.get(key.lower())

        if direction is None:
            self.message("Direction expected.")
            return

        pending = self.pending_directional_command
        self.pending_directional_command = None

        if pending is None:
            return

        pending.handler(direction)

    def start_directional_command(self, command: PendingDirectionalCommand) -> None:
        self.pending_directional_command = command
        self.message(f"Direction for {command.description}?")

    # Movement

    def move(self, direction: Direction) -> None:
        dx, dy = direction
        self.message(f"Move by ({dx}, {dy}).")

    def run(self, direction: Direction) -> None:
        dx, dy = direction
        self.message(f"Run by ({dx}, {dy}).")

    # Directional commands

    def throw_item(self, direction: Direction) -> None:
        dx, dy = direction
        self.message(f"Throw item by ({dx}, {dy}).")

    def forward_until_find(self, direction: Direction) -> None:
        dx, dy = direction
        self.message(f"Move forward until finding something by ({dx}, {dy}).")

    def zap_wand_in_direction(self, direction: Direction) -> None:
        dx, dy = direction
        self.message(f"Zap wand by ({dx}, {dy}).")

    # Immediate commands

    def show_help(self) -> None:
        if self.screen is None:
            return

        self.screen.clear()

        lines = ["Commands:", ""]

        key_width = max(len(key) for key, _description in HELP_COMMANDS)

        for key, description in HELP_COMMANDS:
            lines.append(f"  {key:<{key_width}}  {description}")

        height, width = self.screen.getmaxyx()

        for row, line in enumerate(lines[:height]):
            self.screen.addstr(row, 0, line[: width - 1])

        self.screen.refresh()
        self.screen.getch()
        self.draw_main_screen()

    def identify_object(self) -> None:
        self.message("Identify object.")

    def zap_wand_or_staff(self) -> None:
        self.message("Zap a wand or staff.")

    def go_down_stairs(self) -> None:
        self.message("Go down staircase.")

    def search(self) -> None:
        self.message("Search for traps or secret doors.")

    def rest(self) -> None:
        self.message("Rest for a while.")

    def show_inventory(self) -> None:
        self.message("Show inventory.")

    def show_single_item_inventory(self) -> None:
        self.message("Show inventory for one item.")

    def quaff_potion(self) -> None:
        self.message("Quaff potion.")

    def read_scroll(self) -> None:
        self.message("Read paper.")

    def eat_food(self) -> None:
        self.message("Eat food.")

    def wield_weapon(self) -> None:
        self.message("Wield weapon.")

    def wear_armour(self) -> None:
        self.message("Wear armour.")

    def take_armour_off(self) -> None:
        self.message("Take armour off.")

    def put_on_ring(self) -> None:
        self.message("Put on ring.")

    def remove_ring(self) -> None:
        self.message("Remove ring.")

    def drop_object(self) -> None:
        self.message("Drop object.")

    def call_object(self) -> None:
        self.message("Call object.")

    def examine_options(self) -> None:
        self.message("Examine or set options.")

    def repeat_last_message(self) -> None:
        print(self.last_message)

    def cancel_command(self) -> None:
        self.pending_directional_command = None
        self.message("Cancelled.")

    def print_version(self) -> None:
        self.message("Vallis Magi Rogue prototype version 0.1.")

    def save_game(self) -> None:
        self.message("Save game.")

    def quit_game(self) -> None:
        self.should_quit = True
