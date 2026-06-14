# game_context.py

from collections.abc import Callable
from dataclasses import dataclass

from ..config.config import AppConfig
from ..config.items import AllItems
from ..engine.inventory import InventoryService
from ..protocols.display_protocol import DisplayProtocol
from .player import Player


@dataclass
class GameContext:
    config: AppConfig
    display: DisplayProtocol
    all_items: AllItems
    inventory: InventoryService
    player: Player
    redraw: Callable[[], None]
