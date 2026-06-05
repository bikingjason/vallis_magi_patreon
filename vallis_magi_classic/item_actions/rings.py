from collections.abc import Callable

from ..game_context import GameContext
from ..game_types import ESCAPE
from ..items import ItemDefId, ItemInstanceId
from ..localisation import _

LEFT_HAND = "left"
RIGHT_HAND = "right"


class RingActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context
        self.redraw = False

        self.on_effects: dict[ItemDefId, Callable[[ItemInstanceId], bool]] = {
            # Mundane Rings
            ItemDefId("silver_ring"): self.ring_no_effect_on,
            # Magic Rings
            ItemDefId("ring_of_accuracy"): self.ring_accuracy_on,
            ItemDefId("ring_of_damage"): self.ring_damage_on,
            ItemDefId("ring_of_protection"): self.ring_protection_on,
            ItemDefId("ring_of_regeneration"): self.ring_regeneration_on,
            ItemDefId("ring_of_search"): self.ring_search_on,
            ItemDefId("ring_of_see_invisible"): self.ring_see_invisible_on,
            ItemDefId("ring_of_slow_digestion"): self.ring_slow_digestion_on,
            ItemDefId("ring_of_stealth"): self.ring_stealth_on,
            ItemDefId("ring_of_strength"): self.ring_strength_on,
            ItemDefId("ring_of_sustain_strength"): self.ring_sustain_strength_on,
            # Cursed Rings
            ItemDefId("ring_of_aggravate_monsters"): self.ring_aggravate_monsters_on,
            ItemDefId("ring_of_hunger"): self.ring_hunger_on,
            ItemDefId("ring_of_teleport"): self.ring_teleport_on,
        }

        self.off_effects: dict[ItemDefId, Callable[[ItemInstanceId], bool]] = {
            # Mundane Rings
            ItemDefId("silver_ring"): self.ring_no_effect_off,
            # Magic Rings
            ItemDefId("ring_of_accuracy"): self.ring_accuracy_off,
            ItemDefId("ring_of_damage"): self.ring_damage_off,
            ItemDefId("ring_of_protection"): self.ring_protection_off,
            ItemDefId("ring_of_regeneration"): self.ring_regeneration_off,
            ItemDefId("ring_of_search"): self.ring_search_off,
            ItemDefId("ring_of_see_invisible"): self.ring_see_invisible_off,
            ItemDefId("ring_of_slow_digestion"): self.ring_slow_digestion_off,
            ItemDefId("ring_of_stealth"): self.ring_stealth_off,
            ItemDefId("ring_of_strength"): self.ring_strength_off,
            ItemDefId("ring_of_sustain_strength"): self.ring_sustain_strength_off,
            # Cursed Rings
            ItemDefId("ring_of_aggravate_monsters"): self.ring_aggravate_monsters_off,
            ItemDefId("ring_of_hunger"): self.ring_hunger_off,
            ItemDefId("ring_of_teleport"): self.ring_teleport_off,
        }

    def put_on_ring(self) -> bool:
        ctx = self.context
        player = ctx.player

        item_id, self.redraw = ctx.inventory.pick_item("put on", "ring")
        if item_id is None:
            return self.redraw

        item = ctx.all_items.items[item_id]
        item_def = ctx.all_items.item_defs[item.definition_id]

        if not item_def.is_ring:
            if ctx.config.terse:
                ctx.display.message(_("Not a ring."), wait=self.redraw)
            else:
                ctx.display.message(_("It would be difficult to wrap that around a finger."), wait=self.redraw)
            return self.redraw

        if self.is_wearing_ring(item_id):
            ctx.display.message(_("You are already wearing that."), wait=self.redraw)
            return self.redraw

        hand = self.choose_ring_hand_for_put_on()
        if hand is None:
            return self.redraw

        if hand == LEFT_HAND:
            player.equipment.left_finger = item_id
        else:
            player.equipment.right_finger = item_id

        if item_id in player.inventory.backpack:
            player.inventory.backpack.remove(item_id)

        effect = self.on_effects.get(item.definition_id)

        if effect is None:
            ctx.display.message(_("You feel a strange tingling in your fingers."), wait=self.redraw)
            return self.redraw

        redraw = effect(item_id) | self.redraw
        return redraw

    def remove_ring(self) -> bool:
        ctx = self.context
        player = ctx.player

        if player.equipment.left_finger is None and player.equipment.right_finger is None:
            if ctx.config.terse:
                ctx.display.message(_("No rings."), wait=self.redraw)
            else:
                ctx.display.message(_("You aren't wearing any rings."), wait=self.redraw)
            return False

        hand = self.choose_ring_hand_for_remove()
        if hand is None:
            return False

        if hand == LEFT_HAND:
            item_id = player.equipment.left_finger
        else:
            item_id = player.equipment.right_finger

        if item_id is None:
            ctx.display.message(_("Not wearing such a ring."), wait=self.redraw)
            return False

        item = ctx.all_items.items[item_id]
        item_def = ctx.all_items.item_defs[item.definition_id]

        if item.cursed:
            ctx.display.message(_("You can't. It appears to be cursed."), wait=self.redraw)
            return False

        if hand == LEFT_HAND:
            player.equipment.left_finger = None
        else:
            player.equipment.right_finger = None

        player.inventory.backpack.append(item_id)

        ring_name = item_def.name
        ctx.display.message(_("Was wearing {ring_name}.", ring_name=ring_name), wait=self.redraw)

        effect = self.off_effects.get(item.definition_id)

        if effect is None:
            return False

        return effect(item_id)

    def choose_ring_hand_for_put_on(self) -> str | None:
        player = self.context.player

        left_empty = player.equipment.left_finger is None
        right_empty = player.equipment.right_finger is None

        if left_empty and right_empty:
            return self.get_hand()

        if left_empty:
            return LEFT_HAND

        if right_empty:
            return RIGHT_HAND

        if self.context.config.terse:
            self.context.display.message(_("Wearing two."), wait=self.redraw)
        else:
            self.context.display.message(_("You already have a ring on each hand."), wait=self.redraw)

        return None

    def choose_ring_hand_for_remove(self) -> str | None:
        player = self.context.player

        left_empty = player.equipment.left_finger is None
        right_empty = player.equipment.right_finger is None

        if left_empty and right_empty:
            if self.context.config.terse:
                self.context.display.message(_("No rings."), wait=self.redraw)
            else:
                self.context.display.message(_("You aren't wearing any rings."), wait=self.redraw)
            return None

        if left_empty:
            return RIGHT_HAND

        if right_empty:
            return LEFT_HAND

        return self.get_hand()

    def get_hand(self) -> str | None:
        ctx = self.context

        while True:
            if ctx.config.terse:
                ctx.display.message(_("Left or Right ring? "))
            else:
                ctx.display.message(_("Left hand or right hand? "))

            ch = ctx.display.getch()
            ctx.display.message("")

            if ch in ("l", "L"):
                return LEFT_HAND

            if ch in ("r", "R"):
                return RIGHT_HAND

            if ch == ESCAPE:
                ctx.display.message("")
                return None

            if ctx.config.terse:
                ctx.display.message(_("L or R."), wait=self.redraw)
            else:
                ctx.display.message(_("Please type L or R."), wait=self.redraw)

    def is_wearing_ring(self, item_id: ItemInstanceId) -> bool:
        player = self.context.player

        return item_id in (
            player.equipment.left_finger,
            player.equipment.right_finger,
        )

    # region Mundane Rings

    def ring_no_effect_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("The ring slips onto your finger."), wait=self.redraw)
        return False

    def ring_no_effect_off(self, item_id: ItemInstanceId) -> bool:
        return False

    # endregion

    # region Magic Rings

    def ring_accuracy_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your aim feels steadier."), wait=self.redraw)
        # Later:
        # - add ring hit bonus to combat calculations
        return False

    def ring_accuracy_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your aim feels less certain."), wait=self.redraw)
        # Later:
        # - remove ring hit bonus from combat calculations
        return False

    def ring_damage_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your weapon hand feels more forceful."), wait=self.redraw)
        # Later:
        # - add ring damage bonus to combat calculations
        return False

    def ring_damage_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your weapon hand feels less forceful."), wait=self.redraw)
        # Later:
        # - remove ring damage bonus from combat calculations
        return False

    def ring_protection_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel a little safer."), wait=self.redraw)
        # Later:
        # - add protection bonus to armour/defence calculations
        return False

    def ring_protection_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel a little more exposed."), wait=self.redraw)
        # Later:
        # - remove protection bonus from armour/defence calculations
        return False

    def ring_regeneration_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel your wounds begin to knit more quickly."), wait=self.redraw)
        # Later:
        # - increase HP regeneration
        # - increase food consumption
        return False

    def ring_regeneration_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your body settles back to its normal rhythm."), wait=self.redraw)
        # Later:
        # - remove regeneration effect
        return False

    def ring_search_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your senses feel unusually sharp."), wait=self.redraw)
        # Later:
        # - add passive search chance
        # - increase food consumption occasionally, if following Rogue
        return False

    def ring_search_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your senses dull slightly."), wait=self.redraw)
        # Later:
        # - remove passive search chance
        return False

    def ring_see_invisible_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your eyes tingle."), wait=self.redraw)
        # Later:
        # - add see invisible status
        # - relight/redraw visible area
        return True

    def ring_see_invisible_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your eyes stop tingling."), wait=self.redraw)
        # Later:
        # - remove see invisible status if no other source grants it
        # - relight/redraw visible area
        return True

    def ring_slow_digestion_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your stomach feels strangely calm."), wait=self.redraw)
        # Later:
        # - reduce food consumption
        return False

    def ring_slow_digestion_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your appetite begins to return."), wait=self.redraw)
        # Later:
        # - restore normal food consumption
        return False

    def ring_stealth_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your footsteps seem quieter."), wait=self.redraw)
        # Later:
        # - reduce chance of waking monsters
        return False

    def ring_stealth_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your footsteps sound louder again."), wait=self.redraw)
        # Later:
        # - remove stealth effect
        return False

    def ring_strength_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel stronger."), wait=self.redraw)
        # Later:
        # - apply ring strength bonus
        # - remember to remove it when taking the ring off
        return False

    def ring_strength_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel weaker."), wait=self.redraw)
        # Later:
        # - remove ring strength bonus
        return False

    def ring_sustain_strength_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel fortified."), wait=self.redraw)
        # Later:
        # - protect strength from poison/drain
        # - increase food consumption by 1, if following Rogue
        return False

    def ring_sustain_strength_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel less fortified."), wait=self.redraw)
        # Later:
        # - remove strength protection if no other source grants it
        return False

    # endregion

    # region Cursed Rings

    def ring_aggravate_monsters_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You hear a high-pitched humming noise."), wait=self.redraw)
        # Later:
        # - aggravate all monsters
        return False

    def ring_aggravate_monsters_off(self, item_id: ItemInstanceId) -> bool:
        return False

    def ring_hunger_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You suddenly feel hungry."), wait=self.redraw)
        # Later:
        # - increase food consumption
        return False

    def ring_hunger_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("Your hunger eases."), wait=self.redraw)
        # Later:
        # - remove hunger effect
        return False

    def ring_teleport_on(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel oddly unstable."), wait=self.redraw)
        # Later:
        # - enable random teleportation
        return False

    def ring_teleport_off(self, item_id: ItemInstanceId) -> bool:
        self.context.display.message(_("You feel more firmly anchored."), wait=self.redraw)
        # Later:
        # - disable random teleportation if no other source grants it
        return False

    # endregion
