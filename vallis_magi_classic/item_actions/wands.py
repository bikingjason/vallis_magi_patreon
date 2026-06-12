from collections.abc import Callable

from ..game_context import GameContext
from ..items import ItemDefId, ItemInstanceId
from ..tools.localisation import _


class WandActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context
        self.redraw = False

        self.effects: dict[ItemDefId, Callable[[ItemInstanceId], bool]] = {
            # Mundane Wands
            ItemDefId("wand_nothing"): self.wand_nothing,
            # Directional Monster-effect Wands
            ItemDefId("wand_cancellation"): self.wand_cancellation,
            ItemDefId("wand_polymorph"): self.wand_polymorph,
            ItemDefId("wand_slow_monster"): self.wand_slow_monster,
            ItemDefId("wand_haste_monster"): self.wand_haste_monster,
            ItemDefId("wand_teleport_away"): self.wand_teleport_away,
            ItemDefId("wand_teleport_to"): self.wand_teleport_to,
            # Directional Damage Wands
            ItemDefId("wand_cold"): self.wand_cold,
            ItemDefId("wand_fire"): self.wand_fire,
            ItemDefId("wand_lightning"): self.wand_lightning,
            ItemDefId("wand_magic_missile"): self.wand_magic_missile,
            ItemDefId("wand_striking"): self.wand_striking,
            # Area / Room-effect Wands
            ItemDefId("wand_drain_life"): self.wand_drain_life,
            ItemDefId("wand_light"): self.wand_light,
        }

    def zap_wand(self) -> bool:
        ctx = self.context

        item_id, self.redraw = ctx.inventory.pick_item("zap with", "wand")
        if item_id is None:
            return self.redraw

        item = ctx.all_items.items[item_id]
        item_def = ctx.all_items.item_defs[item.definition_id]

        if not getattr(item_def, "is_wand", False):
            ctx.display.message(_("You can't zap with that!"))
            return self.redraw

        if not self._has_charge(item_id):
            ctx.display.message(_("Nothing happens."), wait=self.redraw)
            return self.redraw

        effect = self.effects.get(item.definition_id)
        if effect is None:
            ctx.display.message(_("What a bizarre schtick!"), wait=self.redraw)
            self._spend_charge(item_id)
            return self.redraw

        # Later:
        # - play a zap sound, if your display/audio layer supports it
        # - ask for direction before calling directional effects
        # - if confused, use a random non-zero direction instead
        redraw = effect(item_id) | self.redraw
        self._spend_charge(item_id)
        return redraw

    def _has_charge(self, item_id: ItemInstanceId) -> bool:
        """Return whether the wand can be used.

        This assumes wand charges are eventually stored on the item instance as
        ``charges``. If that field does not exist yet, wands are treated as
        usable so this file can be added before charge tracking is implemented.
        """
        item = self.context.all_items.items[item_id]
        charges = getattr(item, "charges", None)
        return charges is None or charges > 0

    def _spend_charge(self, item_id: ItemInstanceId) -> None:
        """Spend one charge if the item instance currently tracks charges."""
        item = self.context.all_items.items[item_id]
        charges = getattr(item, "charges", None)
        if charges is not None:
            item.charges = max(0, charges - 1)

    # region Mundane Wands

    def wand_nothing(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("What a bizarre schtick!"), wait=self.redraw)
        return False

    # endregion

    # region Area / Room-effect Wands

    def wand_light(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The room is lit by a shimmering blue light."), wait=self.redraw)
        # Later:
        # - if the hero is in a corridor, show "The corridor glows and then fades"
        # - clear the room's dark flag
        # - relight/redraw the room
        return True

    def wand_drain_life(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You have a tingling feeling."), wait=self.redraw)
        # Later:
        # Original Rogue behaviour:
        # - if the player has fewer than 2 HP, show "You are too weak to use it."
        # - otherwise halve the player's HP
        # - distribute the drained HP among visible monsters in the room, or
        #   adjacent monsters if the player is in a corridor
        # - kill any monsters reduced below 1 HP
        return False

    # endregion

    # region Directional Monster-effect Wands

    def wand_cancellation(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The wand hums briefly, then the air goes still."), wait=self.redraw)
        # Later:
        # - trace a ray in the chosen direction until it reaches a monster
        # - mark that monster as cancelled
        # - remove invisibility from the monster
        return False

    def wand_polymorph(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The air shimmers and twists."), wait=self.redraw)
        # Later:
        # - trace a ray in the chosen direction until it reaches a monster
        # - replace that monster with a random new monster type
        # - preserve the old underlying map character
        # - if the old monster held the player, release the player
        return True

    def wand_slow_monster(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The wand releases a sluggish grey ray."), wait=self.redraw)
        # Later:
        # - trace a ray in the chosen direction until it reaches a monster
        # - if the monster is hasted, remove haste
        # - otherwise apply slow
        # - make the monster notice/run toward the player
        return False

    def wand_haste_monster(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The wand releases a quicksilver ray."), wait=self.redraw)
        # Later:
        # - trace a ray in the chosen direction until it reaches a monster
        # - if the monster is slowed, remove slow
        # - otherwise apply haste
        # - make the monster notice/run toward the player
        return False

    def wand_teleport_away(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Space folds around the target."), wait=self.redraw)
        # Later:
        # - trace a ray in the chosen direction until it reaches a monster
        # - move that monster to a random valid floor position in a random room
        # - make the monster run toward the player afterwards
        return True

    def wand_teleport_to(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Space folds back toward you."), wait=self.redraw)
        # Later:
        # - trace a ray in the chosen direction until it reaches a monster
        # - move that monster to the square adjacent to the player in the ray direction
        # - make the monster run toward the player afterwards
        return True

    # endregion

    # region Directional Damage Wands

    def wand_magic_missile(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The missile vanishes with a puff of smoke."), wait=self.redraw)
        # Later:
        # - ask for / use a direction
        # - animate a 1d4 missile along that path
        # - if it hits a monster and the monster fails its magic save, damage it
        return True

    def wand_striking(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The wand strikes with invisible force."), wait=self.redraw)
        # Later:
        # - affect only the adjacent square in the chosen direction
        # - if a monster is there, fight it using the wand as the weapon
        # - normal damage is roughly 1d8 + 3
        # - about 1 time in 20, use the stronger 3d8 + 9 strike
        return False

    def wand_lightning(self, item_id: ItemInstanceId) -> bool:
        return self._bolt_wand("bolt")

    def wand_fire(self, item_id: ItemInstanceId) -> bool:
        return self._bolt_wand("flame")

    def wand_cold(self, item_id: ItemInstanceId) -> bool:
        return self._bolt_wand("ice")

    def _bolt_wand(self, name: str) -> bool:
        self.context.display.message(_("The {name} shoots from the wand.", name=name), wait=self.redraw)
        # Later:
        # Original Rogue behaviour for lightning/fire/cold:
        # - fire a 6d6 bolt/flame/ice in the chosen direction
        # - animate it with |, -, /, or \\ depending on direction
        # - bounce once when it hits a wall, door, secret door, or blank space
        # - allow it to hit monsters before bouncing
        # - after bouncing, allow it to hit the player
        # - restore the displayed map cells after the bolt finishes
        # TODO will require a screen redraw
        return False

    # endregion
