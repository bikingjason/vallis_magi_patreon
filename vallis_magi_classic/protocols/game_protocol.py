from typing import Protocol


class GameProtocol(Protocol):
    def run_game(self) -> None: ...
