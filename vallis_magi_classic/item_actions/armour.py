from ..config.items import ItemInstanceId
from ..state.game_context import GameContext
from ..tools.localisation import _


class ArmourActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context

    def wear_armour(self) -> bool:
        """
        The player can only wear one suit of armour at a time.
        Wearing armour consumes time and identifies the armour.
        """
        if self.context.player.equipment.body is not None:
            self.context.display.message(_("You are already wearing some. You'll have to take it off first."))

            # Original Rogue sets after = FALSE here.
            return False

        item_id, redraw = self.context.inventory.pick_item("wear", "armour")

        if item_id is None:
            return redraw

        item = self.context.all_items.items[item_id]
        item_def = self.context.all_items.item_defs[item.definition_id]

        if not item_def.is_armour:
            self.context.display.message(_("You can't wear that."), wait=redraw)
            return redraw

        self.waste_time()

        self.context.player.equipment.body = item_id
        # item.known = True

        self.context.display.message(_("You are now wearing {name}.", name=item_def.name), wait=redraw)

        return redraw

    def take_armour_off(self) -> bool:
        """
        Armour can only be removed if dropcheck succeeds.
        This preserves the Rogue behaviour where cursed/stuck equipment
        can prevent removal.
        """
        item_id = self.context.player.equipment.body

        if item_id is None:
            self.context.display.message(_("You aren't wearing any armour."))
            return False

        if not self.dropcheck(item_id):
            return False

        self.context.player.equipment.body = None

        item = self.context.all_items.items[item_id]
        item_def = self.context.all_items.item_defs[item.definition_id]

        self.context.display.message(_("You used to be wearing {name}.", name=item_def.name))

        return False

    def waste_time(self) -> None:
        """
        Equivalent of Rogue's waste_time().

        The player spends a turn while putting armour on.
        """
        # TODO Implement the waste time method
        # self.context.daemons.do_daemons("before")
        # self.context.fuses.do_fuses("before")
        # self.context.daemons.do_daemons("after")
        # self.context.fuses.do_fuses("after")
        pass

    def dropcheck(self, item_id: ItemInstanceId) -> bool:
        """
        Check whether an equipped item can be removed.

        This should eventually contain the cursed-item logic.
        For now it delegates to the inventory/equipment system if present.
        """
        # TODO Add the drop check
        # if hasattr(self.context.inventory, "dropcheck"):
        #     return self.context.inventory.dropcheck(item_id)

        return True
