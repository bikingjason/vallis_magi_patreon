from ..config.config import AppConfig
from ..config.item_store import ItemStore
from ..config.items import ItemDefinition, ItemManager, ItemTag
from ..protocols.display_protocol import DisplayProtocol
from ..state.item_types import ItemInstance, ItemInstanceId, ItemKnowledge
from ..state.player import Player
from ..tools.localisation import _


class InventoryService:
    def __init__(
        self,
        config: AppConfig,
        item_manager: ItemManager,
        item_store: ItemStore,
        item_knowledge: ItemKnowledge,
        display: DisplayProtocol,
        player: Player,
    ) -> None:
        self.config: AppConfig = config
        self.display: DisplayProtocol = display
        self.item_manager = item_manager
        self.item_store = item_store
        self.item_knowledge = item_knowledge
        self.player: Player = player

    def item_matches_type(
        self,
        item_def: ItemDefinition,
        item_type: str,
    ) -> bool:
        """
        Return True if this item definition belongs to the requested inventory group.
        """

        match item_type:
            case "armour":
                return ItemTag.ARMOUR in item_def.tags

            case "food":
                return ItemTag.FOOD in item_def.tags

            case "potion":
                return ItemTag.POTION in item_def.tags

            case "ring":
                return ItemTag.RING in item_def.tags

            case "scroll":
                return ItemTag.SCROLL in item_def.tags

            case "wand":
                return ItemTag.WAND in item_def.tags

            case "weapon":
                return ItemTag.WEAPON in item_def.tags

            case "callable":
                callable_tags = {
                    ItemTag.SCROLL,
                    ItemTag.POTION,
                    ItemTag.RING,
                    ItemTag.WAND,
                }
                return bool(item_def.tags & callable_tags)

            case _:
                raise ValueError(f"Unknown item type: {item_type!r}")

    def inventory_name(
        self,
        item: ItemInstance,
        item_def: ItemDefinition,
    ) -> str:
        """
        Return the display name for an inventory item.

        This is the equivalent of Rogue's inv_name(obj, FALSE).
        You can expand this later for identified/cursed/charges/etc.
        """

        if item.identified:
            name = item_def.name
        else:
            # TODO Need to implement called items, probably in item_knowledge.

            # name = self.all_items.called_names.get(item.definition_id, "")
            # if 0 == len(name):
            # TODO Put the bool tests into a class somewhere
            if ItemTag.POTION in item_def.tags:
                name = _("Unknown Potion")
            elif ItemTag.RING in item_def.tags:
                name = _("Unknown Ring")
            elif ItemTag.SCROLL in item_def.tags:
                name = _("Unknown Scroll")
            elif ItemTag.WAND in item_def.tags:
                name = _("Unknown Wand")
            else:
                raise RuntimeError(f"Unknown item {item_def.name} in inventory_name.")

        if item.quantity > 1:
            return f"{item.quantity}x {name}"

        return name

    def show_inventory_window(
        self,
        lines: list[str],
    ) -> None:
        """
        Display a multi-line inventory list.

        Replace this with your curses/window implementation later.
        """

        self.display.clear()

        height, width = self.display.getmaxyx()

        for row, line in enumerate(lines[:height]):
            self.display.addstr(row, 0, line[: width - 1])

        self.display.refresh()

    def show_inventory(
        self,
        item_ids: list[ItemInstanceId] | None = None,
        item_type: str | None = None,
    ) -> tuple[bool, bool]:
        """
        Show inventory contents.

        This is the Python equivalent of Rogue's inventory(list, type).

        `item_ids` is the list of item instance ids to display.
        If omitted, the player's pack is used.

        `item_type` can be used to filter by item group, for example:
            "armour"
            "food"
            "potion"
            "ring"
            "scroll"
            "wand"
            "weapon"
            "callable"

        Returns True if at least one item was shown, otherwise False.
        """

        player = self.player

        if item_ids is None:
            item_ids = player.inventory.backpack

        lines: list[str] = []

        for index, item_id in enumerate(item_ids):
            item = self.item_store.items[item_id]
            item_def = self.item_manager.item_defs[item.definition_id]

            if item_type is not None and not self.item_matches_type(item_def, item_type):
                continue

            letter = chr(ord("a") + index)
            lines.append(f"{letter}) {self.inventory_name(item, item_def)}")

        if not lines:
            self.display.message(_("You are empty handed.") if item_type is None else _("You don't have anything appropriate."))
            return False, False

        if len(lines) == 1:
            self.display.message(lines[0], wait=True)
            return True, False

        # TODO - Do I need the slow_inventory option?
        # if self.config.slow_invent:
        #     for line in lines:
        #         self.display.message(line)
        # else:
        #     self.show_inventory_window(lines)

        self.show_inventory_window(lines)

        self.display.message(_("--Press space to continue--"), wait=True)

        return True, True

    def pick_item(
        self,
        purpose: str,
        item_type: str | None = None,
    ) -> tuple[ItemInstanceId | None, bool]:
        """
        Ask the player to choose an item from their inventory.

        `purpose` is the verb phrase shown to the player, for example:
            "read"
            "quaff"
            "drop"
            "wear"

        `item_type` can later be used to filter by ISA_GROUPS.
        For now it is accepted but not used.

        Returns the selected ItemInstanceId, or None if the player cancels.
        """

        player = self.player
        redraw = False

        if not player.inventory.backpack:
            self.display.message(_("You aren't carrying anything."))
            return None, redraw

        while True:
            purpose_str = _(purpose)
            prompt = _("Which object do you want to {purpose}? (* for list): ", purpose=purpose_str)
            self.display.message(prompt)

            ch = self.display.getch()
            self.display.message("")

            # Give the player a chance to abort the command.
            if not ch or (ch in ("\x1b", "\x07")):  # ESCAPE or Ctrl-G
                self.after = False
                self.display.message("")
                return None, True

            if ch == "*":
                # TODO - Implement item_type filtering. Do I need both? Probably...
                shown_any, redraw = self.show_inventory(item_type=item_type)

                if not shown_any:
                    self.after = False
                    return None, redraw

                continue

            index = ord(ch) - ord("a")

            if index < 0 or index >= len(player.inventory.backpack):
                last_letter = chr(ord("a") + len(player.inventory.backpack) - 1)
                self.display.message(_("Please specify a letter between 'a' and '{last_letter}'", last_letter=last_letter), wait=True)
                continue

            return player.inventory.backpack[index], redraw

    def remove_or_decrement(self, item_id: ItemInstanceId) -> None:
        """
        Remove an item from the inventory or decrement its count if it is stackable.
        """
        if not item_id:
            return

        item_ids = self.player.inventory.backpack
        if item_id not in item_ids:
            return

        item = self.item_store.items[item_id]

        if 1 >= item.quantity:
            item_ids.remove(item_id)
        else:
            item.quantity -= 1
