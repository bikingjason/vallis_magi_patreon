import curses

from .game import Game

ESCAPE = "\x1b"


def key_code_to_text(key_code: int) -> str | None:
    if key_code == 27:
        return ESCAPE

    if 0 <= key_code <= 255:
        return chr(key_code)

    return None


def run_curses_game(screen: curses.window, game: Game) -> None:
    curses.curs_set(0)
    screen.keypad(True)
    screen.nodelay(False)

    game = Game()
    game.set_screen(screen)
    game.draw_main_screen()

    game.message("Press ? for help.")

    while not game.should_quit:
        key_code = screen.getch()
        key_text = key_code_to_text(key_code)

        if key_text is None:
            continue

        # Ctrl+C
        if key_text == "\x03":
            break

        game.handle_key(key_text)
