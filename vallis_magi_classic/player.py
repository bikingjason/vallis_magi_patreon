from dataclasses import dataclass, field

from .items import AllItems, ItemInstanceId


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


@dataclass
class Player:
    name: str
    inventory: Inventory = field(default_factory=Inventory)
    equipment: Equipment = field(default_factory=Equipment)

    def describe_item(self, all_items: AllItems, item_id: ItemInstanceId | None) -> str:
        if item_id is None:
            return "nothing"

        item = all_items.items[item_id]
        definition = all_items.item_defs[item.definition_id]

        if item.quantity > 1:
            return f"{item.quantity} x {definition.name}"

        return definition.name

    def display_player_welcome(self, all_items: AllItems, new_player: bool) -> None:
        print(f"Welcome {'to' if new_player else 'back to'} the game, {self.name}!\n")
        print("Equipment")
        print("---------")
        print(f"Right hand: {self.describe_item(all_items, self.equipment.right_hand)}")
        print(f"Left hand:  {self.describe_item(all_items, self.equipment.left_hand)}")
        print(f"Body:       {self.describe_item(all_items, self.equipment.body)}")
        print(f"Head:       {self.describe_item(all_items, self.equipment.head)}")
        print()
        print("Backpack")
        print("--------")
        if not self.inventory.backpack:
            print("Empty")
        else:
            for item_id in self.inventory.backpack:
                print(f"- {self.describe_item(all_items, item_id)}")
        print()
