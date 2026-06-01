from collections.abc import Callable

from ..game_context import GameContext
from ..items import ItemDefId, ItemInstanceId


class ScrollActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context

        self.effects: dict[ItemDefId, Callable[[ItemInstanceId], None]] = {
            # Mundane Scroll
            ItemDefId("scroll_blank"): self.scroll_blank,
            ItemDefId("scroll_confuse_monster"): self.scroll_confuse_monster,
            ItemDefId("scroll_enchant_armour"): self.scroll_enchant_armour,
            ItemDefId("scroll_enchant_weapon"): self.scroll_enchant_weapon,
            ItemDefId("scroll_genocide"): self.scroll_genocide,
            ItemDefId("scroll_gold_detection"): self.scroll_gold_detection,
            ItemDefId("scroll_hold_monster"): self.scroll_hold_monster,
            ItemDefId("scroll_identify"): self.scroll_identify,
            ItemDefId("scroll_light"): self.scroll_light,
            ItemDefId("scroll_magic_mapping"): self.scroll_magic_mapping,
            ItemDefId("scroll_remove_curse"): self.scroll_remove_curse,
            ItemDefId("scroll_scare_monster"): self.scroll_scare_monster,
            ItemDefId("scroll_teleportation"): self.scroll_teleportation,
            ItemDefId("scroll_aggravate_monsters"): self.scroll_aggravate_monsters,
            ItemDefId("scroll_create_monster"): self.scroll_create_monster,
            ItemDefId("scroll_sleep"): self.scroll_sleep,
        }

    def read_scroll(self) -> bool:
        ctx = self.context

        item_id = ctx.inventory.pick_item("read", "scroll")
        if item_id is None:
            return False

        item = ctx.all_items.items[item_id]
        item_def = ctx.all_items.item_defs[item.definition_id]

        if not item_def.is_scroll:
            if ctx.config.terse:
                ctx.display.message("Nothing to read.")
            else:
                ctx.display.message("There is nothing on it to read.")
            return False

        ctx.display.message("As you read the scroll, it vanishes.", wait=True)

        effect = self.effects.get(item.definition_id)

        if effect is None:
            ctx.display.message("What a puzzling scroll!")
            return False

        effect(item_id)

        ctx.inventory.remove_or_decrement(item_id)
        ctx.redraw()
        return True

    # region Mundane Scroll

    def scroll_blank(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("This scroll seems to be blank.")

    # endregion

    # region Magic Scrolls

    def scroll_confuse_monster(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("Your hands begin to glow red.")

    def scroll_enchant_armour(self, item_id: ItemInstanceId) -> None:
        player = self.context.player

        if player.equipment.body is None:
            self.context.display.message("You feel a strange sense of loss.")
            return

        armour = self.context.all_items.items[player.equipment.body]
        armour.cursed = False

        self.context.display.message("Your armour glows faintly for a moment.")

    def scroll_enchant_weapon(self, item_id: ItemInstanceId) -> None:
        player = self.context.player

        if player.equipment.right_hand is None:
            self.context.display.message("You feel a strange sense of loss.")
            return

        weapon = self.context.all_items.items[player.equipment.right_hand]
        weapon.cursed = False

        weapon_name = self.context.all_items.item_defs[weapon.definition_id].name
        self.context.display.message(f"Your {weapon_name} glows blue for a moment.")

    def scroll_genocide(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("You have been granted the boon of genocide.", wait=True)
        # Later:
        # self.context.world.genocide()

    def scroll_gold_detection(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("You begin to feel greedy, and you sense gold.")

    def scroll_hold_monster(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("The monsters around you freeze in place.")

    def scroll_light(self, item_id: ItemInstanceId) -> None:
        if self.context.config.terse:
            self.context.display.message("The room is lit.")
        else:
            self.context.display.message("The room is lit by a shimmering blue light.")

    def scroll_identify(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("This scroll is an identify scroll.")
        # Later call identify flow.

    def scroll_magic_mapping(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("Oh, now this scroll has a map on it.")

    def scroll_remove_curse(self, item_id: ItemInstanceId | None) -> None:
        player = self.context.player

        for equipped_item_id in (
            player.equipment.body,
            player.equipment.right_hand,
            player.equipment.left_hand,
            player.equipment.left_finger,
            player.equipment.right_finger,
        ):
            if equipped_item_id is None:
                continue

            item = self.context.all_items.items[equipped_item_id]
            item.cursed = False

        self.context.display.message("You feel as if somebody is watching over you.")

    def scroll_scare_monster(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("You hear maniacal laughter in the distance.")

    def scroll_teleportation(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("You feel strangely displaced.")
        # Later:
        # self.context.world.teleport_player()

    # endregion

    # region Cursed Scrolls

    def scroll_aggravate_monsters(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("You hear a high pitched humming noise.")

    def scroll_create_monster(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("You hear a faint cry of anguish in the distance.")
        # Later this should only be used when no monster can be created.
        # If a monster is created successfully, probably no message is needed.

    def scroll_sleep(self, item_id: ItemInstanceId) -> None:
        self.context.display.message("You fall asleep.")

    # endregion
