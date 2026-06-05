from collections.abc import Callable

from ..game_context import GameContext
from ..items import ItemDefId, ItemInstanceId
from ..localisation import _


class PotionActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context
        self.redraw = False

        self.effects: dict[ItemDefId, Callable[[ItemInstanceId], bool]] = {
            # Mundane Potions
            ItemDefId("potion_of_quench_thirst"): self.potion_quench_thirst,
            # Magic Potions
            ItemDefId("potion_of_extra_healing"): self.potion_extra_healing,
            ItemDefId("potion_of_haste_self"): self.potion_haste_self,
            ItemDefId("potion_of_healing"): self.potion_healing,
            ItemDefId("potion_of_magic_detection"): self.potion_magic_detection,
            ItemDefId("potion_of_monster_detection"): self.potion_monster_detection,
            ItemDefId("potion_of_raise_level"): self.potion_raise_level,
            ItemDefId("potion_of_restore_strength"): self.potion_restore_strength,
            ItemDefId("potion_of_see_invisible"): self.potion_see_invisible,
            ItemDefId("potion_of_strength"): self.potion_strength,
            # Cursed Potions
            ItemDefId("potion_of_blindness"): self.potion_blindness,
            ItemDefId("potion_of_confusion"): self.potion_confusion,
            ItemDefId("potion_of_paralysis"): self.potion_paralysis,
            ItemDefId("potion_of_poison"): self.potion_poison,
        }

    def quaff_potion(self) -> bool:
        ctx = self.context

        item_id, self.redraw = ctx.inventory.pick_item("quaff", "potion")
        if item_id is None:
            return self.redraw

        item = ctx.all_items.items[item_id]
        item_def = ctx.all_items.item_defs[item.definition_id]

        if not item_def.is_potion:
            if ctx.config.terse:
                ctx.display.message(_("That's undrinkable."))
            else:
                ctx.display.message(_("Yuk! Why would you want to drink that?"))
            return self.redraw

        effect = self.effects.get(item.definition_id)

        if effect is None:
            ctx.display.message(_("What an odd tasting potion!"))
            return self.redraw

        redraw = effect(item_id) | self.redraw
        ctx.inventory.remove_or_decrement(item_id)
        return redraw

    # region Mundane Potions

    def potion_quench_thirst(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel your thirst fade away."), wait=self.redraw)
        return False

    # endregion

    # region Magic Potions

    def potion_extra_healing(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You begin to feel much better."), wait=self.redraw)
        # Later:
        # - heal by a larger amount
        # - possibly increase max HP by 1 if overhealed
        # - restore sight if blinded, depending on how closely you follow Rogue
        return False

    def potion_haste_self(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel yourself moving much faster."), wait=self.redraw)
        # Later:
        # - add or extend haste status
        return False

    def potion_healing(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You begin to feel better."), wait=self.redraw)
        # Later:
        # - heal by a smaller amount than extra healing
        # - possibly increase max HP by 1 if overhealed
        # - restore sight if blinded, depending on how closely you follow Rogue
        return False

    def potion_magic_detection(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You have a strange feeling for a moment, then it passes."), wait=self.redraw)
        # Later:
        # If there are magic items on the level:
        # self.context.display.message("You sense the presence of magic on this level.", wait=self.redraw)
        # TODO will require a screen redraw
        return False

    def potion_monster_detection(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You have a strange feeling for a moment, then it passes."), wait=self.redraw)
        # Later:
        # If there are monsters on the level:
        # self.context.display.message("You begin to sense the presence of monsters.", wait=self.redraw)
        # TODO will require a screen redraw
        return False

    def potion_raise_level(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You suddenly feel much more skilful."), wait=self.redraw)
        # Later:
        # - raise player level
        # - adjust HP, combat stats, etc.
        return False

    def potion_restore_strength(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Hey, this tastes great. It makes you feel warm all over."), wait=self.redraw)
        # Later:
        # - restore current strength to maximum strength
        return False

    def potion_see_invisible(self, item_id: ItemInstanceId) -> bool:
        fruit = self.context.config.fruit or "fruit"
        self.context.display.message(_("This potion tastes like {fruit} juice.", fruit=fruit), wait=self.redraw)
        # Later:
        # - add temporary see-invisible status
        # - relight/reveal visible monsters
        # TODO will require a screen redraw
        return False

    def potion_strength(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel stronger, now. What bulging muscles!"), wait=self.redraw)
        # Later:
        # - increase strength by 1
        return False

    # endregion

    # region Cursed Potions

    def potion_blindness(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("A cloak of darkness falls around you."), wait=self.redraw)
        # Later:
        # - add temporary blindness status
        # - redraw visible map accordingly
        # TODO Will require a screen redraw
        return False

    def potion_confusion(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Wait, what's going on here. Huh? What? Who?"), wait=self.redraw)
        # Later:
        # - add or extend confusion status
        return False

    def potion_paralysis(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You can't move."), wait=self.redraw)
        # Later:
        # - prevent commands for HOLDTIME turns
        return False

    def potion_poison(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel very sick now."), wait=self.redraw)
        # Later:
        # - reduce strength unless wearing sustain strength
        return False

    # endregion
