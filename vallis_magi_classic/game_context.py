# game_context.py

from collections.abc import Callable
from dataclasses import dataclass

from .config import AppConfig
from .inventory import InventoryService
from .items import AllItems
from .player import Player
from .protocols.display_protocol import DisplayProtocol


@dataclass
class GameContext:
    config: AppConfig
    display: DisplayProtocol
    all_items: AllItems
    inventory: InventoryService
    player: Player
    redraw: Callable[[], None]
