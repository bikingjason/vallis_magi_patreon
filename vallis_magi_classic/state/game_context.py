# game_context.py

from collections.abc import Callable
from dataclasses import dataclass

from ..config.config import AppConfig
from ..config.item_store import ItemStore
from ..config.items import ItemManager
from ..engine.inventory_services import InventoryService
from ..protocols.display_protocol import DisplayProtocol
from ..state.item_types import ItemKnowledge
from ..state.player import Player


@dataclass
class GameContext:
    config: AppConfig
    display: DisplayProtocol
    item_manager: ItemManager
    item_store: ItemStore
    item_knowledge: ItemKnowledge
    inventory: InventoryService
    player: Player
    redraw: Callable[[], None]
