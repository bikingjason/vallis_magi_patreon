import random
import tomllib
from collections import Counter
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
class ItemProbabilityRange:
    item_def: ItemDefinition
    start: int
    end: int  # exclusive


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
    priority: int = 0
    probability: int = 0
    is_armour: bool = False
    is_food: bool = False
    is_potion: bool = False
    is_ring: bool = False
    is_scroll: bool = False
    is_wand: bool = False
    is_weapon: bool = False


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


ISA_GROUPS: tuple[str, ...] = (
    "is_armour",
    "is_food",
    "is_potion",
    "is_ring",
    "is_scroll",
    "is_wand",
    "is_weapon",
)


class ItemManager:
    def __init__(self, working_dir: Path, items_dir: str, item_files: dict[str, str]) -> None:
        super().__init__()
        self.working_dir = working_dir
        self.items_dir = Path(working_dir / items_dir)
        self.item_files = item_files
        self.item_defs: dict[ItemDefId, ItemDefinition] = {}
        self.item_probability_ranges: dict[str, list[ItemProbabilityRange]] = {}

    def parse_slot(self, value: object) -> ItemSlot | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(f"Item slot must be a string, got {value!r}")

        return ItemSlot(value)

    def build_item_probability_ranges(self) -> None:
        self.item_probability_ranges.clear()

        for isa_name in ISA_GROUPS:
            item_defs = self.get_item_definitions_for_isa(isa_name)

            if not item_defs:
                continue

            item_defs.sort(key=lambda item_def: item_def.priority)

            ranges: list[ItemProbabilityRange] = []
            start = 0

            for item_def in item_defs:
                end = start + item_def.probability

                ranges.append(
                    ItemProbabilityRange(
                        item_def=item_def,
                        start=start,
                        end=end,
                    )
                )

                start = end

            if start != 100:
                raise ValueError(f"{isa_name} probabilities total {start}, expected 100.")

            self.item_probability_ranges[isa_name] = ranges

    def load_item_definitions(self) -> None:

        for item_file in self.item_files:
            file_path = self.items_dir / f"{item_file}.toml"
            with file_path.open("rb") as f:
                data = tomllib.load(f)

            item_section = data.get("items", {})

            if not isinstance(item_section, dict):
                raise ValueError("Expected [items] section in TOML file")

            print(f"Found {len(item_section.items()):>3} entries in {file_path.name}.")

            for raw_id, raw_item in item_section.items():
                if not isinstance(raw_id, str):
                    raise ValueError(f"Item id must be a string, got {raw_id!r}")

                if not isinstance(raw_item, dict):
                    raise ValueError(f"Item {raw_id!r} must be a TOML table")

                item_id = ItemDefId(raw_id)

                self.item_defs[item_id] = ItemDefinition(
                    id=item_id,
                    name=str(raw_item.get("name", raw_id)),
                    weight=float(raw_item.get("weight", 0.0)),
                    slot=self.parse_slot(raw_item.get("slot")),
                    stackable=bool(raw_item.get("stackable", False)),
                    max_stack=int(raw_item.get("max_stack", 1)),
                    attack_bonus=int(raw_item.get("attack_bonus", 0)),
                    armour_bonus=int(raw_item.get("armour_bonus", 0)),
                    priority=int(raw_item.get("priority", 0)),
                    probability=int(raw_item.get("probability", 0)),
                    is_armour=bool(raw_item.get("is_armour", False)),
                    is_food=bool(raw_item.get("is_food", False)),
                    is_potion=bool(raw_item.get("is_potion", False)),
                    is_ring=bool(raw_item.get("is_ring", False)),
                    is_scroll=bool(raw_item.get("is_scroll", False)),
                    is_wand=bool(raw_item.get("is_wand", False)),
                    is_weapon=bool(raw_item.get("is_weapon", False)),
                )

        self.build_item_probability_ranges()

    def verify_item_definitions(self, summary: bool) -> bool:
        """
        Verify all item definition probability groups.

        For each isa group, such as is_armour or is_food, this checks:

        - every item in the group has a priority
        - priorities increase monotonically
        - every item has a probability
        - probabilities sum to 100

        Returns True if every group passes, otherwise False.
        """

        all_ok = True

        for isa_name in ISA_GROUPS:
            group_ok = self.verify_item_definition_group(isa_name, summary)

            if not group_ok:
                all_ok = False

        return all_ok

    def verify_item_definition_group(self, isa_name: str, summary: bool) -> bool:
        items = [item_def for item_def in self.item_defs.values() if bool(getattr(item_def, isa_name, False))]

        print()
        print(f"Verifying {isa_name}")
        print("-" * (len("Verifying ") + len(isa_name)))

        if not items:
            print("No entries found.")
            print("Result: SKIPPED")
            return True

        ok = True

        missing_priority: list[ItemDefinition] = []
        missing_probability: list[ItemDefinition] = []

        for item_def in items:
            if not hasattr(item_def, "priority"):
                missing_priority.append(item_def)

            if not hasattr(item_def, "probability"):
                missing_probability.append(item_def)

        if missing_priority:
            ok = False
            print("Missing priority:")
            for item_def in missing_priority:
                print(f"  {item_def.id}: {item_def.name}")

        if missing_probability:
            ok = False
            print("Missing probability:")
            for item_def in missing_probability:
                print(f"  {item_def.id}: {item_def.name}")

        # If priority or probability is missing, do not try to do the ordered checks.
        if missing_priority or missing_probability:
            print("Result: FAILED")
            return False

        items_by_priority = sorted(
            items,
            key=lambda item_def: int(getattr(item_def, "priority")),
        )

        previous_priority: int | None = None

        for item_def in items_by_priority:
            priority = int(getattr(item_def, "priority"))

            if previous_priority is not None and priority <= previous_priority:
                ok = False
                print(f"Priority order problem: {item_def.id} has priority {priority}, which does not come after {previous_priority}.")

            previous_priority = priority

        probability_total = sum(int(item_def.probability) for item_def in items_by_priority)

        if probability_total != 100:
            ok = False
            print(f"Probability total is {probability_total}, expected 100.")

        if not summary:
            print()
            print("Entries:")

            for item_def in items_by_priority:
                print(f"  {item_def.priority:>3}  {item_def.probability:>3}%  {item_def.id:<30}  {item_def.name}")

        print()
        print(f"Count: {len(items_by_priority)}")
        print(f"Probability total: {probability_total}")
        print(f"Result: {'OK' if ok else 'FAILED'}")

        return ok

    def get_item_definitions_for_isa(self, isa_name: str) -> list[ItemDefinition]:
        """
        Return all item definitions where the requested isa flag is true.

        Example:
            get_item_definitions_for_isa("is_armour")
            get_item_definitions_for_isa("is_food")
            get_item_definitions_for_isa("is_scroll")
        """

        return [item_def for item_def in self.item_defs.values() if bool(getattr(item_def, isa_name, False))]

    def choose_item_definition(
        self,
        isa_name: str,
        *,
        verbose: bool = False,
        rng: random.Random | None = None,
    ) -> ItemDefinition:
        if rng is None:
            rng = random.Random()

        ranges = self.item_probability_ranges.get(isa_name)

        if not ranges:
            raise ValueError(f"No probability ranges found for {isa_name!r}")

        roll = rng.randrange(100)  # 0..99, like Rogue rnd(100)

        if verbose:
            print()
            print(f"Choosing item from {isa_name}")
            print(f"roll={roll}")

        for item_range in ranges:
            if verbose:
                print(f"{item_range.start:>2} <= roll < {item_range.end:<3} {item_range.item_def.name}")

            if item_range.start <= roll < item_range.end:
                if verbose:
                    print(f"Selected: {item_range.item_def.name}")

                return item_range.item_def

        raise RuntimeError(f"Failed to choose item from {isa_name!r}. Roll was {roll}.")

    def create_random_item(self, isa_name: str) -> str:
        item_def = self.choose_item_definition(isa_name)
        return item_def.name

    def test_random_item_creation_for_isa(
        self,
        isa_name: str,
        *,
        trials: int = 1000,
        rng: random.Random | None = None,
    ) -> None:

        if rng is None:
            rng = random.Random()

        item_defs = self.get_item_definitions_for_isa(isa_name)

        if not item_defs:
            print()
            print(f"{isa_name}")
            print("-" * len(isa_name))
            print("No items found.")
            return

        item_defs.sort(key=lambda item_def: item_def.priority)

        counts: Counter[str] = Counter()

        for _ in range(trials):
            item_name = self.create_random_item(isa_name)
            counts[item_name] += 1

        print()
        print(f"{isa_name}  Trials={trials}")
        print("-" * (len(isa_name)))
        print()

        print(f"{'Priority':>8}  {'Item':<30}  {'Count':>8}  {'Observed':>9}  {'Config':>8}")

        print(f"{'-' * 8}  {'-' * 30}  {'-' * 8}  {'-' * 9}  {'-' * 8}")

        for item_def in item_defs:
            count = counts[item_def.name]
            observed_percentage = count / trials * 100.0
            print(f"{item_def.priority:>8}  {item_def.name:<30}  {count:>8}  {observed_percentage:>8.2f}%  {item_def.probability:>7}%")
        print()

    def test_random_item_creation(
        self,
        *,
        trials: int = 1000,
        rng: random.Random | None = None,
    ) -> None:
        """
        Run repeated random item creation tests for every isa group.

        For each isa group:
        - create `trials` random items
        - tally how often each item was created
        - print count, observed percentage, and configured probability
        """

        if rng is None:
            rng = random.Random()

        for isa_name in ISA_GROUPS:
            self.test_random_item_creation_for_isa(
                isa_name,
                trials=trials,
                rng=rng,
            )
