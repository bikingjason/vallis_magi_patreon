from ..config.items import ItemDefinition, ItemTag
from ..state.game_context import GameContext
from ..state.item_types import ItemDefId, ItemInstanceId
from ..tools.localisation import _


class InventoryActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context

    def drop_object(self) -> bool:
        """
        Pick an item from the backpack and drop it on the player's current tile.
        If dropping from a stack, split off one item unless it is a weapon stack,
        matching the original Rogue behaviour.
        """
        if not self.can_drop_on_current_tile():
            self.context.display.message(_("There is something there already."))
            return False

        item_id, redraw = self.context.inventory.pick_item("drop", None)

        if item_id is None:
            return redraw

        if not self.dropcheck(item_id):
            return redraw

        item = self.context.item_store.items[item_id]
        item_def = self.context.item_manager.item_defs[item.definition_id]

        if item.quantity >= 2 and (ItemTag.WEAPON not in item_def.tags):
            dropped_item_id = self.split_one_from_stack(item_id)
        else:
            dropped_item_id = item_id
            self.context.inventory.remove_or_decrement(item_id)

        self.drop_item_at_player(dropped_item_id)

        # dropped_item = self.context.all_items.items[dropped_item_id]
        # dropped_item_def = self.context.all_items.item_defs[dropped_item.definition_id]

        self.context.display.message(_("Dropped {name}", name=self.inventory_name(dropped_item_id, drop=True)))

        return redraw

    def call_object(self) -> bool:
        """
        Let the player assign a remembered name to an unidentified object type.

        This is the behaviour behind Rogue's 'call' command. It is mainly useful
        for potions, scrolls, rings, and wands/sticks whose true identity is not
        known yet.
        """
        item_id, redraw = self.context.inventory.pick_item("call", "callable")

        if item_id is None:
            return redraw

        item = self.context.item_store.items[item_id]
        item_def = self.context.item_manager.item_defs[item.definition_id]

        if not self.can_call_item(item_def):
            self.context.display.message(_("You can't call that anything."))
            return redraw

        current_name = self.get_called_name(item.definition_id)

        if current_name:
            prompt = _("Was called {current_name}. Call it: ", current_name=current_name)
        else:
            prompt = _("Call it: ")

        called_name = self.read_line(prompt).strip()

        if not called_name:
            return redraw

        self.set_called_name(item.definition_id, called_name)

        return redraw

    def dropcheck(self, item_id: ItemInstanceId) -> bool:
        """
        Checks whether an equipped item can be dropped, unwielded, removed,
        or taken off. Cursed equipped items cannot be removed.
        """
        # item = self.context.all_items.items[item_id]

        if not self.is_equipped(item_id):
            return True

        if self.is_cursed(item_id):
            self.context.display.message(_("You can't. It appears to be cursed."))
            return False

        equipment = self.context.player.equipment

        if equipment.right_hand == item_id:
            equipment.right_hand = None
        elif equipment.left_hand == item_id:
            equipment.left_hand = None
        elif equipment.body == item_id:
            self.waste_time()
            equipment.body = None
        elif equipment.left_finger == item_id:
            self.remove_ring_effect(item_id)
            equipment.left_finger = None
        elif equipment.right_finger == item_id:
            self.remove_ring_effect(item_id)
            equipment.right_finger = None

        return True

    def can_drop_on_current_tile(self) -> bool:
        """
        In Rogue, you can only drop onto FLOOR or PASSAGE.

        In your version this should check whether the player's current tile can
        accept an item and does not already contain an object.
        """
        # TODO Implement the drop check
        # if hasattr(self.context, "level") and hasattr(self.context.level, "can_drop_item_at"):
        # return self.context.level.can_drop_item_at(self.context.player.position)

        return True

    def drop_item_at_player(self, item_id: ItemInstanceId) -> None:
        """
        Link the item into the level object list at the player's current position.
        """
        # TODO Implement the drop action
        # item = self.context.all_items.items[item_id]
        # item.position = self.context.player.position

        # if hasattr(self.context, "level") and hasattr(self.context.level, "add_item"):
        #     self.context.level.add_item(item_id, self.context.player.position)
        #     return

        # if hasattr(self.context, "level") and hasattr(self.context.level, "items"):
        #     self.context.level.items.append(item_id)
        #     return

        raise NotImplementedError("No level item-drop API has been implemented yet.")

    def split_one_from_stack(self, item_id: ItemInstanceId) -> ItemInstanceId:
        """
        Split one item off an inventory stack and return the new item id.

        This corresponds to the C code creating a new item, decrementing the
        original stack, and setting the dropped object's count to 1.
        """
        # TODO Implement the split action
        # if hasattr(self.context.all_items, "split_stack"):
        #     return self.context.all_items.split_stack(item_id, 1)

        raise NotImplementedError("Implement all_items.split_stack(item_id, count) to support dropping one item from a stack.")

    def is_equipped(self, item_id: ItemInstanceId) -> bool:
        equipment = self.context.player.equipment

        return (
            equipment.right_hand == item_id
            or equipment.left_hand == item_id
            or equipment.body == item_id
            or equipment.left_finger == item_id
            or equipment.right_finger == item_id
        )

    def is_cursed(self, item_id: ItemInstanceId) -> bool:
        item = self.context.item_store.items[item_id]
        item_def = self.context.item_manager.item_defs[item.definition_id]

        return bool(
            getattr(item, "is_cursed", False)
            or getattr(item, "cursed", False)
            or getattr(item_def, "is_cursed", False)
            or getattr(item_def, "cursed", False)
        )

    def remove_ring_effect(self, item_id: ItemInstanceId) -> None:
        """
        Placeholder for Rogue's ring-removal side effects.

        Original Rogue removed effects such as add-strength and see-invisible
        here. This can stay empty until rings are implemented.
        """
        pass

    def waste_time(self) -> None:
        """
        Same idea as armour.waste_time().
        """
        # TODO Implement daemons/fuses when available.
        pass

    def can_call_item(self, item_def: ItemDefinition) -> bool:
        """
        Only unidentified magical item types can be given names.
        """
        callable_tags = {
            ItemTag.SCROLL,
            ItemTag.POTION,
            ItemTag.RING,
            ItemTag.WAND,
        }
        return bool(item_def.tags & callable_tags)

    def get_called_name(self, definition_id: ItemDefId) -> str:
        return self.context.item_knowledge.called_names.get(definition_id, "")

    def set_called_name(self, definition_id: ItemDefId, called_name: str) -> None:
        self.context.item_knowledge.called_names[definition_id] = called_name

    def read_line(self, prompt: str) -> str:
        return self.context.display.prompt(prompt)

    def inventory_name(self, item_id: ItemInstanceId, drop: bool = False) -> str:
        # TODO Should this just be the one in inventory.py, or should that be using this?
        # """
        # Prefer your existing inventory naming function if you have one.
        # """
        # if hasattr(self.context.inventory, "inventory_name"):
        #     return self.context.inventory.inventory_name(item_id, drop=drop)

        item = self.context.item_store.items[item_id]
        item_def = self.context.item_manager.item_defs[item.definition_id]

        name = self.get_called_name(item.definition_id)
        # TODO Need to check if it is identified, if not then the randomly generated name is used.
        if 0 == len(name):
            name = item_def.name

        if item.quantity > 1:
            name = f"{item.quantity}x {name}"
        else:
            name = _("a {name}", anme=name)

        if not drop:
            name = name[:1].upper() + name[1:] + "."

        return name
