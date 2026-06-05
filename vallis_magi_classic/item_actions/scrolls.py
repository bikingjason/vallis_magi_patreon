from collections.abc import Callable

from ..game_context import GameContext
from ..items import ItemDefId, ItemInstanceId
from ..localisation import _


class ScrollActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context
        self.redraw = False

        self.effects: dict[ItemDefId, Callable[[ItemInstanceId], bool]] = {
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

        item_id, self.redraw = ctx.inventory.pick_item("read", "scroll")
        if item_id is None:
            return self.redraw

        item = ctx.all_items.items[item_id]
        item_def = ctx.all_items.item_defs[item.definition_id]

        if not item_def.is_scroll:
            if ctx.config.terse:
                ctx.display.message(_("Nothing to read."))
            else:
                ctx.display.message(_("There is nothing on it to read."))
            return self.redraw

        ctx.display.message(_("As you read the scroll, it vanishes."), wait=self.redraw)

        effect = self.effects.get(item.definition_id)

        if effect is None:
            ctx.display.message(_("What a puzzling scroll!"))
            return self.redraw

        redraw = effect(item_id) | self.redraw
        ctx.inventory.remove_or_decrement(item_id)
        return redraw

    # region Mundane Scroll

    def scroll_blank(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("This scroll seems to be blank."))
        return False

    # endregion

    # region Magic Scrolls

    def scroll_confuse_monster(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your hands begin to glow red."), wait=self.redraw)
        return False

    def scroll_enchant_armour(self, item_id: ItemInstanceId) -> bool:
        player = self.context.player

        if player.equipment.body is None:
            self.context.display.message(_("You feel a strange sense of loss."), wait=self.redraw)
            return False

        armour = self.context.all_items.items[player.equipment.body]
        armour.cursed = False

        self.context.display.message(_("Your armour glows faintly for a moment."), wait=self.redraw)
        return False

    def scroll_enchant_weapon(self, item_id: ItemInstanceId) -> bool:
        player = self.context.player

        if player.equipment.right_hand is None:
            self.context.display.message(_("You feel a strange sense of loss."), wait=self.redraw)
            return False

        weapon = self.context.all_items.items[player.equipment.right_hand]
        weapon.cursed = False

        weapon_name = self.context.all_items.item_defs[weapon.definition_id].name
        self.context.display.message(_("Your {weapon_name} glows blue for a moment.", weapon_name=weapon_name), wait=self.redraw)
        return False

    def scroll_genocide(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You have been granted the boon of genocide."), wait=self.redraw)
        # Later:
        # self.context.world.genocide()
        # TODO will require a screen redraw
        return False

    def scroll_gold_detection(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You begin to feel greedy, and you sense gold."), wait=self.redraw)
        # TODO will require a screen redraw
        return False

    def scroll_hold_monster(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The monsters around you freeze in place."), wait=self.redraw)
        return False

    def scroll_light(self, item_id: ItemInstanceId) -> bool:
        if self.context.config.terse:
            self.context.display.message(_("The room is lit."), wait=self.redraw)
        else:
            self.context.display.message(_("The room is lit by a shimmering blue light."), wait=self.redraw)
        # TODO will require a screen redraw
        return False

    def scroll_identify(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("This scroll is an identify scroll."), wait=self.redraw)
        # Later call identify flow.
        return False

    def scroll_magic_mapping(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Oh, now this scroll has a map on it."), wait=self.redraw)
        # TODO will require a screen redraw
        return False

    def scroll_remove_curse(self, item_id: ItemInstanceId | None) -> bool:
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

        self.context.display.message(_("You feel as if somebody is watching over you."), wait=self.redraw)
        return False

    def scroll_scare_monster(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You hear maniacal laughter in the distance."), wait=self.redraw)
        return False

    def scroll_teleportation(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel strangely displaced."), wait=self.redraw)
        # Later:
        # self.context.world.teleport_player()
        # TODO will require a screen redraw
        return False

    # endregion

    # region Cursed Scrolls

    def scroll_aggravate_monsters(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You hear a high pitched humming noise."), wait=self.redraw)
        return False

    def scroll_create_monster(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You hear a faint cry of anguish in the distance."), wait=self.redraw)
        # Later this should only be used when no monster can be created.
        # If a monster is created successfully, probably no message is needed.
        # TODO will require a screen redraw
        return False

    def scroll_sleep(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You fall asleep."), wait=self.redraw)
        return False

    # endregion
