from dataclasses import dataclass, field

from .game_types import Position
from .items import AllItems, ItemDefId, ItemInstanceId


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
    def __init__(self, name: str) -> None:
        super().__init__()

        self.name: str = name
        self.inventory: Inventory = Inventory()
        self.equipment: Equipment = Equipment()

        self.position: Position = (0, 0)

    @staticmethod
    def create_new_player(name: str, all_items: AllItems) -> Player:

        food = all_items.new_item(ItemDefId("food"), 2)
        ring_mail = all_items.new_item(ItemDefId("ring_mail"))
        long_sword = all_items.new_item(ItemDefId("long_sword"))

        # Test items
        potion_of_quench_thirst = all_items.new_item(ItemDefId("potion_of_quench_thirst"))
        ring_of_slow_digestion = all_items.new_item(ItemDefId("ring_of_slow_digestion"))
        scroll_genocide = all_items.new_item(ItemDefId("scroll_genocide"))
        wand_cold = all_items.new_item(ItemDefId("wand_cold"))
        scale_mail = all_items.new_item(ItemDefId("scale_mail"))
        bow = all_items.new_item(ItemDefId("bow"))

        # All the itmes that the Player has at the start are identified.
        potion_item = all_items.items[potion_of_quench_thirst]
        potion_def = all_items.item_defs[potion_item.definition_id]
        potion_def.is_identified = True
        ring_item = all_items.items[ring_of_slow_digestion]
        ring_def = all_items.item_defs[ring_item.definition_id]
        ring_def.is_identified = True
        scroll_item = all_items.items[scroll_genocide]
        scroll_def = all_items.item_defs[scroll_item.definition_id]
        scroll_def.is_identified = True
        wand_item = all_items.items[wand_cold]
        wand_def = all_items.item_defs[wand_item.definition_id]
        wand_def.is_identified = True

        player = Player(name)

        player.inventory.backpack.append(food)
        player.inventory.backpack.append(ring_of_slow_digestion)
        player.inventory.backpack.append(potion_of_quench_thirst)
        player.inventory.backpack.append(scroll_genocide)
        player.inventory.backpack.append(wand_cold)
        player.inventory.backpack.append(scale_mail)
        player.inventory.backpack.append(bow)
        player.equipment.body = ring_mail
        player.equipment.right_hand = long_sword

        return player
