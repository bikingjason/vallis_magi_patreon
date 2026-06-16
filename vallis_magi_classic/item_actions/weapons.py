from dataclasses import dataclass
from random import randrange

from ..config.items import ItemTag
from ..state.game_context import GameContext
from ..state.item_types import ItemInstanceId
from ..tools.localisation import _

NO_LAUNCHER = None


@dataclass(frozen=True)
class WeaponInit:
    damage: str
    throw_damage: str
    launcher: str | None = NO_LAUNCHER
    is_many: bool = False
    is_missile: bool = False


WEAPON_INITIAL_STATS: dict[str, WeaponInit] = {
    "mace": WeaponInit("2d4", "1d3"),
    "long_sword": WeaponInit("1d10", "1d2"),
    "short_bow": WeaponInit("1d1", "1d1"),
    "arrow": WeaponInit("1d1", "1d6", launcher="short_bow", is_many=True, is_missile=True),
    "dagger": WeaponInit("1d6", "1d4", is_missile=True),
    "rock": WeaponInit("1d2", "1d4", launcher="sling", is_many=True, is_missile=True),
    "two_handed_sword": WeaponInit("3d6", "1d2"),
    "sling": WeaponInit("0d0", "0d0"),
    "dart": WeaponInit("1d1", "1d3", is_many=True, is_missile=True),
    "crossbow": WeaponInit("1d1", "1d1"),
    "crossbow_bolt": WeaponInit("1d2", "1d10", launcher="crossbow", is_many=True, is_missile=True),
    "spear": WeaponInit("1d8", "1d6", is_missile=True),
}


class WeaponActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context

    def wield_weapon(self) -> bool:
        """
        The currently wielded weapon is first checked with dropcheck, so cursed
        or stuck equipment can prevent switching. Selecting the current item is
        treated as no action, matching Rogue's is_current() check.
        """
        # TODO Need to pick hand to wield weapon.
        current_weapon = self.context.player.equipment.right_hand

        if current_weapon is not None and not self.dropcheck(current_weapon):
            return False

        item_id, redraw = self.context.inventory.pick_item("wield", "weapon")

        if item_id is None:
            return redraw

        item = self.context.item_store.items[item_id]
        item_def = self.context.item_manager.item_defs[item.definition_id]

        if ItemTag.ARMOUR in item_def.tags:
            self.context.display.message(_("You can't wield armour."))
            return redraw

        if self.is_current(item_id):
            return redraw

        self.context.player.equipment.right_hand = item_id
        self.context.display.message(_("You are now wielding {name}", name=item_def.name))

        return redraw

    def throw_weapon(self, y_delta: int, x_delta: int) -> bool:
        # TODO Can this be called, there is no 't' Throw option...?
        """
        This handles inventory selection and stack splitting. The actual flight,
        monster hit, and floor drop are delegated to project systems if they
        exist, because those depend on your map/combat implementation.
        """
        item_id, redraw = self.context.inventory.pick_item("throw", "weapon")

        if item_id is None:
            return redraw

        if not self.dropcheck(item_id) or self.is_current(item_id):
            return redraw

        thrown_item_id = self.remove_one_for_throwing(item_id)
        self.do_motion(thrown_item_id, y_delta, x_delta)

        hit = self.hit_monster_at_item_position(thrown_item_id)
        if not hit:
            self.fall(thrown_item_id, print_message=True)

        return True

    def remove_one_for_throwing(self, item_id: ItemInstanceId) -> ItemInstanceId:
        """
        Remove one item from inventory for throwing.

        If the item is stacked, the stack count is reduced and a single-item
        copy is created when the item manager supports it. Otherwise the item
        itself is removed and thrown.
        """
        # TODO Handle removing an item.
        # item = self.context.all_items.items[item_id]
        # count = getattr(item, "count", 1)

        # if count < 2:
        #     self.context.inventory.remove_item(item_id)
        #     return item_id

        # item.count -= 1

        # if hasattr(self.context.all_items, "copy_item"):
        #     thrown_item_id = self.context.all_items.copy_item(item_id)
        #     thrown_item = self.context.all_items.items[thrown_item_id]
        #     thrown_item.count = 1
        #     return thrown_item_id

        # Fallback: no item-copy support yet. Return the original item and let
        # the caller/project replace this once the item manager has cloning.
        return item_id

    def do_motion(self, item_id: ItemInstanceId, y_delta: int, x_delta: int) -> None:
        """
        The original animates the object from the hero position until it hits a
        blocked tile or door. Delegate to a map/projectile system if present.
        """
        # TODO Implement weapon motion
        # if hasattr(self.context, "projectiles"):
        #     self.context.projectiles.do_motion(item_id, y_delta, x_delta)
        pass

    def fall(self, item_id: ItemInstanceId, print_message: bool) -> None:
        """
        The original tries to put the item on a nearby floor/passages tile. If
        no position exists, the item vanishes.
        """
        # TODO
        # if hasattr(self.context, "level") and hasattr(self.context.level, "drop_near_player"):
        #     if self.context.level.drop_near_player(item_id):
        #         return

        if print_message:
            item = self.context.item_store.items[item_id]
            item_def = self.context.item_manager.item_defs[item.definition_id]
            self.context.display.message(_("Your {name} vanishes as it hits the ground.", anme=item_def.name))

        # TODO Implement weapon discard
        # if hasattr(self.context.all_items, "discard_item"):
        #     self.context.all_items.discard_item(item_id)

    def init_weapon(self, item_id: ItemInstanceId) -> None:
        """
        This applies default damage, thrown damage, launcher, missile flags, and
        stack count for the classic Rogue weapons, provided the item instance has
        matching mutable fields.
        """
        item = self.context.item_store.items[item_id]
        item_def = self.context.item_manager.item_defs[item.definition_id]

        stats = WEAPON_INITIAL_STATS.get(str(item.definition_id))
        if stats is None:
            stats = WEAPON_INITIAL_STATS.get(item_def.name.lower().replace(" ", "_"))
        if stats is None:
            return

        # TODO Handle weapon stats
        # item.damage = stats.damage
        # item.throw_damage = stats.throw_damage
        # item.launcher = stats.launcher
        # item.is_many = stats.is_many
        # item.is_missile = stats.is_missile

        # if stats.is_many:
        #     item.count = randrange(8) + 8
        #     if hasattr(self.context.all_items, "new_group"):
        #         item.group = self.context.all_items.new_group()
        # else:
        #     item.count = 1

    def hit_monster_at_item_position(self, item_id: ItemInstanceId) -> bool:
        # TODO
        # if hasattr(self.context, "combat") and hasattr(self.context.combat, "hit_monster_with_item"):
        #     return self.context.combat.hit_monster_with_item(item_id)

        return False

    def fallpos(self, y: int, x: int, passages: bool) -> tuple[int, int] | None:
        """
        Uses reservoir sampling, as the C version does with rnd(++cnt) == 0, so
        each valid neighbouring tile has an equal chance of being chosen.
        """
        selected: tuple[int, int] | None = None
        count = 0

        for new_y in range(y - 1, y + 2):
            for new_x in range(x - 1, x + 2):
                if self.is_player_position(new_y, new_x):
                    continue
                if not self.can_fall_on(new_y, new_x, passages):
                    continue

                count += 1
                if randrange(count) == 0:
                    selected = (new_y, new_x)

        return selected

    def dropcheck(self, item_id: ItemInstanceId) -> bool:
        """
        Check whether an equipped item can be removed or thrown.
        """
        # TODO Add the cursed/stuck item check when equipment curses exist.
        # if hasattr(self.context.inventory, "dropcheck"):
        #     return self.context.inventory.dropcheck(item_id)
        return True

    def is_current(self, item_id: ItemInstanceId) -> bool:
        equipment = self.context.player.equipment
        # TODO Weapon coul dbe in either hand.
        return item_id in {
            equipment.right_hand,
            equipment.body,
            getattr(equipment, "left_ring", None),
            getattr(equipment, "right_ring", None),
        }

    def is_player_position(self, y: int, x: int) -> bool:
        player = self.context.player
        return getattr(player, "y", None) == y and getattr(player, "x", None) == x

    def can_fall_on(self, y: int, x: int, passages: bool) -> bool:
        if not hasattr(self.context, "level"):
            return False

        # TODO
        # level: Any = self.context.level

        # if hasattr(level, "offmap") and level.offmap(y, x):
        #     return False

        # if hasattr(level, "tile_at"):
        #     tile = level.tile_at(y, x)
        #     return tile == "floor" or (passages and tile == "passage")

        return False


def num(n1: int, n2: int) -> str:
    """
    Equivalent of Rogue's num() helper for armour/weapon bonuses.
    """
    if n1 == 0 and n2 == 0:
        return "+0"

    if n2 == 0:
        return f"{n1:+d}"

    return f"{n1:+d},{n2:+d}"
