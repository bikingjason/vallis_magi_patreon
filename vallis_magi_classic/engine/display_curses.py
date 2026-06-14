import curses

from ..protocols.display_protocol import DisplayProtocol
from ..protocols.game_protocol import GameProtocol
from ..state.game_types import CTRL_C, CTRL_R, ESCAPE
from ..tools.localisation import _


class DisplayCurses(DisplayProtocol):
    def __init__(self) -> None:
        super().__init__()

        self.last_message: str = ""
        self._screen: curses.window | None = None

        self._max_x: int | None = None
        self._max_y: int | None = None
        self._message_line: int | None = None

    @property
    def screen(self) -> curses.window:
        if self._screen is None:
            raise RuntimeError("DisplayCurses screen has not been initialized. Call DisplayCurses.set_display_limits() first.")

        return self._screen

    @property
    def max_x(self) -> int:
        if self._max_x is None:
            raise RuntimeError("DisplayCurses screen.width has not been initialized. Call DisplayCurses.set_display_limits() first.")

        return self._max_x

    @property
    def max_y(self) -> int:
        if self._max_y is None:
            raise RuntimeError("DisplayCurses screen.height has not been initialized. Call DisplayCurses.set_message_line() first.")

        return self._max_y

    @property
    def message_line(self) -> int:
        if self._message_line is None:
            raise RuntimeError("DisplayCurses screen.message_line has not been initialized. Call DisplayCurses.set_message_line() first.")

        return self._message_line

    def _setup(self, screen: curses.window) -> None:
        curses.raw()
        curses.curs_set(0)
        screen.keypad(True)
        screen.nodelay(False)
        self._screen = screen

    def _key_code_to_text(self, key_code: int) -> str | None:
        if key_code == 27:
            return ESCAPE

        if key_code == 3:
            return CTRL_C

        if key_code == 18:
            return CTRL_R

        if 0 <= key_code <= 255:
            return chr(key_code)

        return None

    def _run_curses(self, screen: curses.window, game: GameProtocol) -> None:
        self._setup(screen)
        game.run_game()

    def getch(self) -> str | None:
        key_code = self.screen.getch()
        return self._key_code_to_text(key_code)

    def prompt(self, prompt: str) -> str:
        """
        Display a prompt and read a line of text from the player.
        """
        self.clear_message_line()
        self.screen.addstr(self.message_line, 0, prompt)
        self.screen.refresh()

        curses.echo()
        curses.curs_set(1)

        try:
            y = self.message_line
            x = len(prompt)

            # Read up to 60 characters after the prompt.
            raw = self.screen.getstr(y, x, 60)

            return raw.decode("utf-8").strip()

        finally:
            curses.noecho()
            curses.curs_set(0)
            self.clear_message_line()
            self.screen.refresh()

    def clear_message_line(self) -> None:
        self.screen.move(self.message_line, 0)
        self.clrtoeol()

    def clear(self) -> None:
        self.screen.clear()

    def refresh(self) -> None:
        self.screen.refresh()

    def getmaxyx(self) -> tuple[int, int]:
        height, width = self.screen.getmaxyx()
        return height, width

    def move(self, new_y: int, new_x: int) -> None:
        self.screen.move(new_y, new_x)

    def clrtoeol(self) -> None:
        self.screen.clrtoeol()

    def addstr(self, y: int, x: int, text: str) -> None:
        self.screen.addstr(y, x, text)

    def set_display_limits(self, max_x: int, max_y: int) -> None:
        self._max_x = max_x
        self._max_y = max_y

    def set_message_line(self, y: int) -> None:
        self._message_line = y

    def message(self, text: str, wait: bool = False) -> None:

        self.last_message = text

        self.clear_message_line()

        screen = self.screen
        if wait:
            continue_str = _("continue")
            screen.addstr(self.message_line, 0, f"{text} <{continue_str}>"[: self.max_x - 1])
        else:
            screen.addstr(self.message_line, 0, text[: self.max_x - 1])
        screen.refresh()

        # After updating wait for the user to press a key so that we know they have read the message.
        if wait:
            self.getch()

    def run(self, game: GameProtocol) -> None:
        curses.wrapper(self._run_curses, game)
