import curses

from .protocols.display_protocol import CTRL_C, ESCAPE, DisplayProtocol
from .protocols.game_protocol import GameProtocol


class DisplayCurses(DisplayProtocol):
    def __init__(self) -> None:
        super().__init__()

        self._screen: curses.window | None = None

    @property
    def screen(self) -> curses.window:
        if self._screen is None:
            raise RuntimeError("DisplayCurses screen has not been initialized. Call DisplayCurses.run(game) before using display methods.")

        return self._screen

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

        if 0 <= key_code <= 255:
            return chr(key_code)

        return None

    def _run_curses(self, screen: curses.window, game: GameProtocol) -> None:
        self._setup(screen)
        game.run_game()

    def getch(self) -> str | None:
        key_code = self.screen.getch()
        return self._key_code_to_text(key_code)

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

    def message(self, text: str) -> None:
        self.last_message = text

        screen = self.screen
        height, width = screen.getmaxyx()
        row = height - 1

        screen.move(row, 0)
        screen.clrtoeol()
        screen.addstr(row, 0, text[: width - 1])
        screen.refresh()

    def run(self, game: GameProtocol) -> None:
        curses.wrapper(self._run_curses, game)
