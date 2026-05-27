from dataclasses import dataclass, field

from .items import AllItems, ItemDefId
from .player import Player


@dataclass
class GameState:
    all_items: AllItems
    player: Player = field(default_factory=lambda: Player(name="Player"))

    def create_new_player(self, name: str, all_items: AllItems) -> None:

        food = all_items.new_item(ItemDefId("food"), 2)
        ring_mail = all_items.new_item(ItemDefId("ring_mail"))
        long_sword = all_items.new_item(ItemDefId("long_sword"))

        self.player.name = name

        self.player.inventory.backpack.append(food)
        self.player.equipment.body = ring_mail
        self.player.equipment.right_hand = long_sword
