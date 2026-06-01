from dataclasses import dataclass, field

from .game_types import Position
from .items import ItemInstanceId
from .protocols.display_protocol import DisplayProtocol


@dataclass
class Equipment:
    head: ItemInstanceId | None = None
    body: ItemInstanceId | None = None

    left_hand: ItemInstanceId | None = None
    right_hand: ItemInstanceId | None = None

    left_finger: ItemInstanceId | None = None
    right_finger: ItemInstanceId | None = None


@dataclass
class Inventory:
    backpack: list[ItemInstanceId] = field(default_factory=list)


class Player:
    def __init__(self, name: str, display: DisplayProtocol) -> None:
        super().__init__()
        self.display = display

        self.name: str = name
        self.inventory: Inventory = Inventory()
        self.equipment: Equipment = Equipment()

        self.position: Position = (0, 0)
