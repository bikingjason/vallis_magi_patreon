import curses

from .protocols.display_protocol import ESCAPE, DisplayProtocol
from .protocols.game_protocol import GameProtocol


class DisplayCurses(DisplayProtocol):
    def __init__(self) -> None:
        super().__init__()

        # self.game: GameProtocol | None = None
        self.screen: curses.window | None = None

    def _setup(self, screen: curses.window) -> None:
        curses.curs_set(0)

        self.screen = screen
        self.screen.keypad(True)
        self.screen.nodelay(False)

    def _key_code_to_text(self, key_code: int) -> str | None:
        if key_code == 27:
            return ESCAPE

        if 0 <= key_code <= 255:
            return chr(key_code)

        return None

    def _run_curses(self, screen: curses.window, game: GameProtocol) -> None:
        self._setup(screen)
        game.run_game()

    def getch(self) -> str | None:
        if self.screen is None:
            return

        key_code = self.screen.getch()
        return self._key_code_to_text(key_code)

    def clear(self) -> None:
        if self.screen is None:
            return

        self.screen.clear()

    def refresh(self) -> None:
        if self.screen is None:
            return

        self.screen.refresh()

    def getmaxyx(self) -> tuple[int, int]:
        if self.screen is None:
            return 0, 0

        height, width = self.screen.getmaxyx()
        return height, width

    def move(self, new_y: int, new_x: int) -> None:
        if self.screen is None:
            return

        self.screen.move(new_y, new_x)

    def clrtoeol(self) -> None:
        if self.screen is None:
            return

        self.screen.clrtoeol()

    def addstr(self, y: int, x: int, text: str) -> None:
        if self.screen is None:
            return

        self.screen.addstr(y, x, text)

    def run(self, game: GameProtocol) -> None:
        curses.wrapper(self._run_curses, game)
