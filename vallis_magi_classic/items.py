import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import NewType

ItemDefId = NewType("ItemDefId", str)
ItemInstanceId = NewType("ItemInstanceId", int)


class ItemSlot(Enum):
    HEAD = "head"
    BODY = "body"
    HAND = "hand"
    FINGER = "finger"


@dataclass(frozen=True)
class ItemDefinition:
    id: ItemDefId
    name: str
    weight: float
    slot: ItemSlot | None = None
    stackable: bool = False
    max_stack: int = 1
    attack_bonus: int = 0
    damage_bonus: int = 0
    armour_bonus: int = 0


@dataclass
class ItemInstance:
    id: ItemInstanceId
    definition_id: ItemDefId
    quantity: int = 1

    # Per-copy state goes here.
    identified: bool = False
    cursed: bool = False
    charges: int | None = None
    durability: int | None = None


@dataclass
class AllItems:
    item_defs: dict[ItemDefId, ItemDefinition]
    items: dict[ItemInstanceId, ItemInstance]
    next_item_id: int = 1

    def new_item(
        self,
        definition_id: ItemDefId,
        quantity: int = 1,
    ) -> ItemInstanceId:
        item_id = ItemInstanceId(self.next_item_id)
        self.next_item_id += 1

        self.items[item_id] = ItemInstance(
            id=item_id,
            definition_id=definition_id,
            quantity=quantity,
        )

        return item_id


class ItemManager:
    def __init__(self, working_dir: Path, items_dir: str, item_files: dict[str, str]) -> None:
        super().__init__()
        self.working_dir = working_dir
        self.items_dir = Path(working_dir / items_dir)
        self.item_files = item_files

    def parse_slot(self, value: object) -> ItemSlot | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(f"Item slot must be a string, got {value!r}")

        return ItemSlot(value)

    def load_item_definitions(self) -> dict[ItemDefId, ItemDefinition]:

        item_defs: dict[ItemDefId, ItemDefinition] = {}

        for item_file in self.item_files:
            file_path = self.items_dir / f"{item_file}.toml"
            with file_path.open("rb") as f:
                data = tomllib.load(f)

            item_section = data.get("items", {})

            if not isinstance(item_section, dict):
                raise ValueError("Expected [items] section in TOML file")

            for raw_id, raw_item in item_section.items():
                if not isinstance(raw_id, str):
                    raise ValueError(f"Item id must be a string, got {raw_id!r}")

                if not isinstance(raw_item, dict):
                    raise ValueError(f"Item {raw_id!r} must be a TOML table")

                item_id = ItemDefId(raw_id)

                item_defs[item_id] = ItemDefinition(
                    id=item_id,
                    name=str(raw_item.get("name", raw_id)),
                    weight=float(raw_item.get("weight", 0.0)),
                    slot=self.parse_slot(raw_item.get("slot")),
                    stackable=bool(raw_item.get("stackable", False)),
                    max_stack=int(raw_item.get("max_stack", 1)),
                    attack_bonus=int(raw_item.get("attack_bonus", 0)),
                    armour_bonus=int(raw_item.get("armour_bonus", 0)),
                )

        return item_defs
