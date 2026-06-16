from dataclasses import dataclass, field
from enum import Enum
from typing import NewType

ItemDefId = NewType("ItemDefId", str)
ItemInstanceId = NewType("ItemInstanceId", int)


class ItemSlot(Enum):
    HEAD = "head"
    BODY = "body"
    HAND = "hand"
    FINGER = "finger"


class ItemTag(Enum):
    ARMOUR = "armour"
    FOOD = "food"
    POTION = "potion"
    RING = "ring"
    SCROLL = "scroll"
    WAND = "wand"
    WEAPON = "weapon"
    AMMUNITION = "ammunition"


@dataclass(frozen=True)
class RandomTableComponent:
    group: str
    priority: int
    probability: int


@dataclass(frozen=True)
class StackComponent:
    max_stack: int


@dataclass(frozen=True)
class EquipmentComponent:
    slot: ItemSlot


@dataclass(frozen=True)
class WeaponComponent:
    weapon_category: str
    damage: str | None = None
    thrown_damage: str | None = None
    hit_bonus: int = 0
    damage_bonus: int = 0
    speed_penalty: int = 0
    hands: int = 1
    can_throw: bool = False
    ammunition_type: str | None = None


@dataclass(frozen=True)
class ArmourComponent:
    armour_bonus: int
    armour_class: int
    movement_penalty: int = 0
    stealth_penalty: int = 0


@dataclass(frozen=True)
class FoodComponent:
    nutrition: int


@dataclass(frozen=True)
class ChargesComponent:
    min_charges: int
    max_charges: int


@dataclass(frozen=True)
class IdentificationComponent:
    starts_identified: bool = True
    appearance_group: str | None = None


@dataclass(frozen=True)
class ItemDefinition:
    id: ItemDefId
    name: str
    description: str = ""
    usage: str = ""
    weight: float = 0.0
    value: int = 0

    tags: frozenset[ItemTag] = field(default_factory=frozenset)

    random_table: RandomTableComponent | None = None
    stack: StackComponent | None = None
    equipment: EquipmentComponent | None = None
    weapon: WeaponComponent | None = None
    armour: ArmourComponent | None = None
    food: FoodComponent | None = None
    charges: ChargesComponent | None = None
    identification: IdentificationComponent = field(default_factory=IdentificationComponent)


@dataclass
class ItemInstance:
    id: ItemInstanceId
    definition_id: ItemDefId
    quantity: int = 1

    # Per-copy state.
    identified: bool = False
    cursed: bool = False
    charges: int | None = None
    durability: int | None = None


@dataclass
class ItemKnowledge:
    called_names: dict[ItemDefId, str] = field(default_factory=dict)
    identified_defs: set[ItemDefId] = field(default_factory=set)

    def call_item(self, definition_id: ItemDefId, name: str) -> None:
        self.called_names[definition_id] = name

    def get_called_name(self, definition_id: ItemDefId) -> str | None:
        return self.called_names.get(definition_id)

    def identify(self, definition_id: ItemDefId) -> None:
        self.identified_defs.add(definition_id)

    def is_identified(self, definition_id: ItemDefId) -> bool:
        return definition_id in self.identified_defs
