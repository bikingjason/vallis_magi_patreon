import random
from dataclasses import dataclass, field

from ..state.item_types import ItemDefId, ItemDefinition, ItemInstance, ItemInstanceId
from .items import ItemManager


@dataclass
class ItemStore:
    item_manager: ItemManager
    items: dict[ItemInstanceId, ItemInstance] = field(default_factory=dict)
    next_item_id: int = 1

    def new_item(
        self,
        definition_id: ItemDefId,
        quantity: int = 1,
        *,
        rng: random.Random | None = None,
    ) -> ItemInstanceId:
        if rng is None:
            rng = random.Random()

        item_def = self.item_manager.item_defs[definition_id]

        if item_def.stack is None and quantity != 1:
            raise ValueError(f"{definition_id!r} is not stackable")

        if item_def.stack is not None and quantity > item_def.stack.max_stack:
            raise ValueError(f"{definition_id!r} quantity {quantity} exceeds max stack {item_def.stack.max_stack}")

        charges: int | None = None
        if item_def.charges is not None:
            charges = rng.randint(
                item_def.charges.min_charges,
                item_def.charges.max_charges,
            )

        item_id = ItemInstanceId(self.next_item_id)
        self.next_item_id += 1

        self.items[item_id] = ItemInstance(
            id=item_id,
            definition_id=definition_id,
            quantity=quantity,
            identified=item_def.identification.starts_identified,
            cursed=False,
            charges=charges,
        )

        return item_id

    def new_random_item(
        self,
        random_table: str,
        *,
        rng: random.Random | None = None,
    ) -> ItemInstanceId:
        if rng is None:
            rng = random.Random()

        item_def = self.item_manager.choose_item_definition(
            random_table,
            rng=rng,
        )

        return self.new_item(
            item_def.id,
            rng=rng,
        )

    def get_item(self, item_id: ItemInstanceId) -> ItemInstance:
        return self.items[item_id]

    def get_definition(self, item_id: ItemInstanceId) -> ItemDefinition:
        item = self.items[item_id]
        return self.item_manager.item_defs[item.definition_id]
