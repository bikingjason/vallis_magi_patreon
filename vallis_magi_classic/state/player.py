from dataclasses import dataclass, field

from ..config.item_store import ItemStore
from ..config.items import ItemDefId
from ..state.item_types import ItemInstanceId, ItemKnowledge
from .game_types import Position


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

        self.hit_points = 11
        self.max_hit_points = 15
        self.level = 2
        self.gold = 5

    @staticmethod
    def create_new_player(
        name: str,
        item_store: ItemStore,
        item_knowledge: ItemKnowledge,
    ) -> Player:
        food = item_store.new_item(ItemDefId("food"), 2)
        ring_mail = item_store.new_item(ItemDefId("ring_mail"))
        long_sword = item_store.new_item(ItemDefId("long_sword"))

        # Test items
        potion_of_quench_thirst = item_store.new_item(ItemDefId("potion_of_quench_thirst"))
        ring_of_slow_digestion = item_store.new_item(ItemDefId("ring_of_slow_digestion"))
        scroll_genocide = item_store.new_item(ItemDefId("scroll_genocide"))
        wand_cold = item_store.new_item(ItemDefId("wand_cold"))
        scale_mail = item_store.new_item(ItemDefId("scale_mail"))
        bow = item_store.new_item(ItemDefId("bow"))

        # All the items that the player starts with are identified.
        item_knowledge.identify(ItemDefId("potion_of_quench_thirst"))
        item_knowledge.identify(ItemDefId("ring_of_slow_digestion"))
        item_knowledge.identify(ItemDefId("scroll_genocide"))
        item_knowledge.identify(ItemDefId("wand_cold"))

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
