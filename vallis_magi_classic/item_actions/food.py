from random import randint

from ..game_context import GameContext
from ..items import ItemInstanceId
from ..tools.localisation import _

HUNGERTIME = 1300
STOMACHSIZE = 2000


class FoodActions:
    def __init__(self, context: GameContext) -> None:
        self.context = context

    def eat_food(self) -> bool:
        """
        The player selects a food item from the backpack, eats one ration,
        restores hunger, and removes the item when the stack is exhausted.
        """
        item_id, redraw = self.context.inventory.pick_item("eat", "food")

        if item_id is None:
            return redraw

        item = self.context.all_items.items[item_id]
        item_def = self.context.all_items.item_defs[item.definition_id]

        if not item_def.is_food:
            self.context.display.message(_("Ugh, you would get ill if you ate that."))
            return redraw

        if randint(0, 99) > 70:
            self.context.display.message(_("Yuk, this food tastes awful."))
            # TODO Add food effect
            # self.context.player.stats.exp += 1
            # self.check_level()
        else:
            self.context.display.message(_("Yum, that tasted good."))

        # TODO Add food effect
        # self.context.player.food_left += HUNGERTIME + randint(0, 399) - 200

        # if self.context.player.food_left > STOMACHSIZE:
        #     self.context.player.food_left = STOMACHSIZE

        # self.context.player.hungry_state = 0

        # if self.context.player.equipment.weapon == item_id:
        #     self.context.player.equipment.weapon = None

        self.consume_one(item_id)

        return redraw

    def consume_one(self, item_id: ItemInstanceId) -> None:
        # item = self.context.all_items.items[item_id]

        # item.count -= 1

        # if item.count > 0:
        #     return

        self.context.inventory.remove_or_decrement(item_id)

        # if hasattr(self.context.all_items, "discard_item"):
        #     self.context.all_items.discard_item(item_id)

    # def check_level(self) -> None:
    #     if hasattr(self.context.player, "check_level"):
    #         self.context.player.check_level()
    #         return

    #     if hasattr(self.context, "check_level"):
    #         self.context.check_level()
