import copy
import random
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..state.item_types import (
    ArmourComponent,
    ChargesComponent,
    EquipmentComponent,
    FoodComponent,
    IdentificationComponent,
    ItemDefId,
    ItemDefinition,
    ItemSlot,
    ItemTag,
    RandomTableComponent,
    StackComponent,
    WeaponComponent,
)

RANDOM_TABLES: tuple[str, ...] = (
    "armour",
    "food",
    "potions",
    "rings",
    "scrolls",
    "wands",
    "weapons",
)


@dataclass(frozen=True)
class ItemProbabilityRange:
    item_def: ItemDefinition
    start: int
    end: int  # exclusive


class ItemManager:
    def __init__(
        self,
        working_dir: Path,
        items_dir: str,
        item_files: dict[str, str] | list[str] | tuple[str, ...],
    ) -> None:
        self.working_dir = working_dir
        self.items_dir = working_dir / items_dir
        self.item_files = item_files

        self.item_defs: dict[ItemDefId, ItemDefinition] = {}
        self.item_probability_ranges: dict[str, list[ItemProbabilityRange]] = {}

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def load_item_definitions(self) -> None:
        self.item_defs.clear()
        self.item_probability_ranges.clear()

        for item_file in self._iter_item_file_names():
            file_path = self.items_dir / f"{item_file}.toml"

            with file_path.open("rb") as f:
                data = tomllib.load(f)

            defaults = self._read_defaults(data, file_path)
            item_section = data.get("items", {})

            if not isinstance(item_section, dict):
                raise ValueError(f"{file_path}: expected [items] section to be a table")

            for raw_id, raw_item in item_section.items():
                if not isinstance(raw_id, str):
                    raise ValueError(f"{file_path}: item id must be a string, got {raw_id!r}")

                if not isinstance(raw_item, dict):
                    raise ValueError(f"{file_path}: item {raw_id!r} must be a TOML table")

                item_def = self._build_item_definition(
                    file_path=file_path,
                    raw_id=raw_id,
                    raw_item=raw_item,
                    defaults=defaults,
                )

                if item_def.id in self.item_defs:
                    raise ValueError(f"{file_path}: duplicate item definition {item_def.id!r}")

                self.item_defs[item_def.id] = item_def

        self.build_item_probability_ranges()

    def build_item_probability_ranges(self) -> None:
        self.item_probability_ranges.clear()

        table_names = sorted({item_def.random_table.group for item_def in self.item_defs.values() if item_def.random_table is not None})

        for table_name in table_names:
            item_defs = self.get_item_definitions_for_random_table(table_name)

            if not item_defs:
                continue

            item_defs.sort(key=lambda item_def: item_def.random_table.priority)  # type: ignore[union-attr]

            ranges: list[ItemProbabilityRange] = []
            start = 0

            for item_def in item_defs:
                assert item_def.random_table is not None

                end = start + item_def.random_table.probability

                ranges.append(
                    ItemProbabilityRange(
                        item_def=item_def,
                        start=start,
                        end=end,
                    )
                )

                start = end

            if start != 100:
                raise ValueError(f"{table_name} probabilities total {start}, expected 100.")

            self.item_probability_ranges[table_name] = ranges

    def verify_item_definitions(self, summary: bool) -> bool:
        all_ok = True

        table_names = sorted({item_def.random_table.group for item_def in self.item_defs.values() if item_def.random_table is not None})

        for table_name in table_names:
            group_ok = self.verify_random_table(table_name, summary)

            if not group_ok:
                all_ok = False

        return all_ok

    def verify_random_table(self, table_name: str, summary: bool) -> bool:
        items = self.get_item_definitions_for_random_table(table_name)

        print()
        print(f"Verifying {table_name}")
        print("-" * (len("Verifying ") + len(table_name)))

        if not items:
            print("No entries found.")
            print("Result: SKIPPED")
            return True

        ok = True

        items_by_priority = sorted(
            items,
            key=lambda item_def: item_def.random_table.priority if item_def.random_table is not None else -1,
        )

        previous_priority: int | None = None
        seen_priorities: set[int] = set()

        for item_def in items_by_priority:
            if item_def.random_table is None:
                ok = False
                print(f"Missing random table: {item_def.id}: {item_def.name}")
                continue

            priority = item_def.random_table.priority
            probability = item_def.random_table.probability

            if priority in seen_priorities:
                ok = False
                print(f"Duplicate priority: {item_def.id} has priority {priority}.")

            seen_priorities.add(priority)

            if previous_priority is not None and priority <= previous_priority:
                ok = False
                print(f"Priority order problem: {item_def.id} has priority {priority}, which does not come after {previous_priority}.")

            if probability <= 0:
                ok = False
                print(f"Probability problem: {item_def.id} has probability {probability}.")

            previous_priority = priority

        probability_total = sum(item_def.random_table.probability for item_def in items_by_priority if item_def.random_table is not None)

        if probability_total != 100:
            ok = False
            print(f"Probability total is {probability_total}, expected 100.")

        if not summary:
            print()
            print("Entries:")

            for item_def in items_by_priority:
                assert item_def.random_table is not None

                print(f"  {item_def.random_table.priority:>3}  {item_def.random_table.probability:>3}%  {item_def.id:<30}  {item_def.name}")

        print()
        print(f"Count: {len(items_by_priority)}")
        print(f"Probability total: {probability_total}")
        print(f"Result: {'OK' if ok else 'FAILED'}")

        return ok

    def get_item_definitions_for_random_table(self, table_name: str) -> list[ItemDefinition]:
        return [item_def for item_def in self.item_defs.values() if item_def.random_table is not None and item_def.random_table.group == table_name]

    def get_item_definitions_with_tag(self, tag: ItemTag) -> list[ItemDefinition]:
        return [item_def for item_def in self.item_defs.values() if tag in item_def.tags]

    def choose_item_definition(
        self,
        table_name: str,
        *,
        verbose: bool = False,
        rng: random.Random | None = None,
    ) -> ItemDefinition:
        if rng is None:
            rng = random.Random()

        ranges = self.item_probability_ranges.get(table_name)

        if not ranges:
            raise ValueError(f"No probability ranges found for random table {table_name!r}")

        roll = rng.randrange(100)

        if verbose:
            print()
            print(f"Choosing item from {table_name}")
            print(f"roll={roll}")

        for item_range in ranges:
            if verbose:
                print(f"{item_range.start:>2} <= roll < {item_range.end:<3} {item_range.item_def.name}")

            if item_range.start <= roll < item_range.end:
                if verbose:
                    print(f"Selected: {item_range.item_def.name}")

                return item_range.item_def

        raise RuntimeError(f"Failed to choose item from {table_name!r}. Roll was {roll}.")

    def create_random_item(
        self,
        table_name: str,
        *,
        rng: random.Random | None = None,
    ) -> ItemDefinition:
        return self.choose_item_definition(table_name, rng=rng)

    def test_random_item_creation_for_table(
        self,
        table_name: str,
        *,
        trials: int = 1000,
        rng: random.Random | None = None,
    ) -> None:
        if rng is None:
            rng = random.Random()

        item_defs = self.get_item_definitions_for_random_table(table_name)

        if not item_defs:
            print()
            print(f"{table_name}")
            print("-" * len(table_name))
            print("No items found.")
            return

        item_defs.sort(key=lambda item_def: item_def.random_table.priority)  # type: ignore[union-attr]

        counts: Counter[str] = Counter()

        for _ in range(trials):
            item_def = self.create_random_item(table_name, rng=rng)
            counts[item_def.name] += 1

        print()
        print(f"{table_name}  Trials={trials}")
        print("-" * len(table_name))
        print()

        print(f"{'Priority':>8}  {'Item':<30}  {'Count':>8}  {'Observed':>9}  {'Config':>8}")
        print(f"{'-' * 8}  {'-' * 30}  {'-' * 8}  {'-' * 9}  {'-' * 8}")

        for item_def in item_defs:
            assert item_def.random_table is not None

            count = counts[item_def.name]
            observed_percentage = count / trials * 100.0

            print(
                f"{item_def.random_table.priority:>8}  "
                f"{item_def.name:<30}  "
                f"{count:>8}  "
                f"{observed_percentage:>8.2f}%  "
                f"{item_def.random_table.probability:>7}%"
            )

        print()

    def test_random_item_creation(
        self,
        *,
        trials: int = 1000,
        rng: random.Random | None = None,
    ) -> None:
        if rng is None:
            rng = random.Random()

        table_names = sorted(self.item_probability_ranges)

        for table_name in table_names:
            self.test_random_item_creation_for_table(
                table_name,
                trials=trials,
                rng=rng,
            )

    # ---------------------------------------------------------------------
    # TOML loading
    # ---------------------------------------------------------------------

    def _iter_item_file_names(self) -> list[str]:
        if isinstance(self.item_files, dict):
            return list(self.item_files)

        return list(self.item_files)

    def _read_defaults(
        self,
        data: dict[str, Any],
        file_path: Path,
    ) -> dict[str, dict[str, Any]]:
        raw_defaults = data.get("default", {})

        if raw_defaults is None:
            return {}

        if not isinstance(raw_defaults, dict):
            raise ValueError(f"{file_path}: expected [default] to be a table")

        defaults: dict[str, dict[str, Any]] = {}

        for default_name, default_data in raw_defaults.items():
            if not isinstance(default_name, str):
                raise ValueError(f"{file_path}: default name must be a string, got {default_name!r}")

            if not isinstance(default_data, dict):
                raise ValueError(f"{file_path}: [default.{default_name}] must be a table")

            defaults[default_name] = copy.deepcopy(default_data)

        return defaults

    def _build_item_definition(
        self,
        *,
        file_path: Path,
        raw_id: str,
        raw_item: dict[str, Any],
        defaults: dict[str, dict[str, Any]],
    ) -> ItemDefinition:
        merged = self._merge_inherited_defaults(
            file_path=file_path,
            raw_id=raw_id,
            raw_item=raw_item,
            defaults=defaults,
        )

        item_id = ItemDefId(raw_id)

        tags = self._parse_tags(merged.get("tags", []), file_path, raw_id)
        equipment = self._parse_equipment_component(merged, file_path, raw_id)
        stack = self._parse_stack_component(merged, file_path, raw_id)
        random_table = self._parse_random_table_component(merged, file_path, raw_id)

        weapon = self._parse_weapon_component(merged.get("weapon"), file_path, raw_id)
        armour = self._parse_armour_component(merged.get("armour"), file_path, raw_id)
        food = self._parse_food_component(merged.get("food"), file_path, raw_id)
        charges = self._parse_charges_component(merged.get("charges"), file_path, raw_id)
        identification = self._parse_identification_component(merged, file_path, raw_id)

        # Convenience: if the item has a component, make sure the tag exists.
        if weapon is not None:
            tags = tags | frozenset({ItemTag.WEAPON})

        if armour is not None:
            tags = tags | frozenset({ItemTag.ARMOUR})

        if food is not None:
            tags = tags | frozenset({ItemTag.FOOD})

        return ItemDefinition(
            id=item_id,
            name=str(merged.get("name", raw_id)),
            description=str(merged.get("description", "")),
            usage=str(merged.get("usage", "")),
            weight=float(merged.get("weight", 0.0)),
            value=int(merged.get("value", 0)),
            tags=tags,
            random_table=random_table,
            stack=stack,
            equipment=equipment,
            weapon=weapon,
            armour=armour,
            food=food,
            charges=charges,
            identification=identification,
        )

    def _merge_inherited_defaults(
        self,
        *,
        file_path: Path,
        raw_id: str,
        raw_item: dict[str, Any],
        defaults: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        inherits = raw_item.get("inherits", [])

        if isinstance(inherits, str):
            inherits = [inherits]

        if not isinstance(inherits, list):
            raise ValueError(f"{file_path}: item {raw_id!r} inherits must be a string or list of strings")

        merged: dict[str, Any] = {}

        for inherit_name in inherits:
            if not isinstance(inherit_name, str):
                raise ValueError(f"{file_path}: item {raw_id!r} inherits contains non-string value {inherit_name!r}")

            inherited = defaults.get(inherit_name)

            if inherited is None:
                raise ValueError(f"{file_path}: item {raw_id!r} inherits unknown default {inherit_name!r}")

            self._deep_update(merged, inherited)

        item_without_inherits = copy.deepcopy(raw_item)
        item_without_inherits.pop("inherits", None)

        self._deep_update(merged, item_without_inherits)

        return merged

    def _deep_update(
        self,
        target: dict[str, Any],
        source: dict[str, Any],
    ) -> None:
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = copy.deepcopy(value)

    # ---------------------------------------------------------------------
    # Component parsers
    # ---------------------------------------------------------------------

    def _parse_slot(
        self,
        value: object,
        file_path: Path,
        raw_id: str,
    ) -> ItemSlot | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(f"{file_path}: item {raw_id!r} slot must be a string, got {value!r}")

        try:
            return ItemSlot(value)
        except ValueError as exc:
            valid = ", ".join(slot.value for slot in ItemSlot)
            raise ValueError(f"{file_path}: item {raw_id!r} slot {value!r} is invalid. Valid slots: {valid}") from exc

    def _parse_tags(
        self,
        value: object,
        file_path: Path,
        raw_id: str,
    ) -> frozenset[ItemTag]:
        if value is None:
            return frozenset()

        if not isinstance(value, list):
            raise ValueError(f"{file_path}: item {raw_id!r} tags must be a list of strings")

        tags: set[ItemTag] = set()

        for raw_tag in value:
            if not isinstance(raw_tag, str):
                raise ValueError(f"{file_path}: item {raw_id!r} tag must be a string, got {raw_tag!r}")

            try:
                tags.add(ItemTag(raw_tag))
            except ValueError as exc:
                valid = ", ".join(tag.value for tag in ItemTag)
                raise ValueError(f"{file_path}: item {raw_id!r} tag {raw_tag!r} is invalid. Valid tags: {valid}") from exc

        return frozenset(tags)

    def _parse_equipment_component(
        self,
        item: dict[str, Any],
        file_path: Path,
        raw_id: str,
    ) -> EquipmentComponent | None:
        slot = self._parse_slot(item.get("slot"), file_path, raw_id)

        if slot is None:
            return None

        return EquipmentComponent(slot=slot)

    def _parse_stack_component(
        self,
        item: dict[str, Any],
        file_path: Path,
        raw_id: str,
    ) -> StackComponent | None:
        stackable = bool(item.get("stackable", False))
        max_stack = int(item.get("max_stack", 1))

        if max_stack < 1:
            raise ValueError(f"{file_path}: item {raw_id!r} max_stack must be >= 1")

        if stackable and max_stack == 1:
            raise ValueError(f"{file_path}: item {raw_id!r} is stackable but max_stack is 1")

        if not stackable and max_stack != 1:
            # You can make this an error if you prefer stricter config.
            stackable = True

        if not stackable:
            return None

        return StackComponent(max_stack=max_stack)

    def _parse_random_table_component(
        self,
        item: dict[str, Any],
        file_path: Path,
        raw_id: str,
    ) -> RandomTableComponent | None:
        table_name = item.get("random_table")

        has_priority = "priority" in item
        has_probability = "probability" in item

        if table_name is None and not has_priority and not has_probability:
            return None

        if table_name is None:
            raise ValueError(f"{file_path}: item {raw_id!r} has priority/probability but no random_table")

        if not isinstance(table_name, str):
            raise ValueError(f"{file_path}: item {raw_id!r} random_table must be a string")

        if not has_priority:
            raise ValueError(f"{file_path}: item {raw_id!r} is in random_table {table_name!r} but has no priority")

        if not has_probability:
            raise ValueError(f"{file_path}: item {raw_id!r} is in random_table {table_name!r} but has no probability")

        priority = int(item["priority"])
        probability = int(item["probability"])

        if priority < 1:
            raise ValueError(f"{file_path}: item {raw_id!r} priority must be >= 1")

        if probability < 1:
            raise ValueError(f"{file_path}: item {raw_id!r} probability must be >= 1")

        return RandomTableComponent(
            group=table_name,
            priority=priority,
            probability=probability,
        )

    def _parse_weapon_component(
        self,
        value: object,
        file_path: Path,
        raw_id: str,
    ) -> WeaponComponent | None:
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError(f"{file_path}: item {raw_id!r} [weapon] must be a table")

        category = value.get("category", value.get("weapon_category"))

        if category is None:
            raise ValueError(f"{file_path}: item {raw_id!r} weapon component has no category")

        if not isinstance(category, str):
            raise ValueError(f"{file_path}: item {raw_id!r} weapon category must be a string")

        ammunition_type = value.get("ammunition_type", value.get("requires_ammunition"))

        if ammunition_type is not None and not isinstance(ammunition_type, str):
            raise ValueError(f"{file_path}: item {raw_id!r} ammunition_type must be a string")

        return WeaponComponent(
            weapon_category=category,
            damage=self._optional_str(value.get("damage")),
            thrown_damage=self._optional_str(value.get("thrown_damage")),
            hit_bonus=int(value.get("hit_bonus", 0)),
            damage_bonus=int(value.get("damage_bonus", 0)),
            speed_penalty=int(value.get("speed_penalty", 0)),
            hands=int(value.get("hands", 1)),
            can_throw=bool(value.get("can_throw", False)),
            ammunition_type=ammunition_type,
        )

    def _parse_armour_component(
        self,
        value: object,
        file_path: Path,
        raw_id: str,
    ) -> ArmourComponent | None:
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError(f"{file_path}: item {raw_id!r} [armour] must be a table")

        if "armour_bonus" not in value:
            raise ValueError(f"{file_path}: item {raw_id!r} armour component has no armour_bonus")

        if "armour_class" not in value:
            raise ValueError(f"{file_path}: item {raw_id!r} armour component has no armour_class")

        return ArmourComponent(
            armour_bonus=int(value["armour_bonus"]),
            armour_class=int(value["armour_class"]),
            movement_penalty=int(value.get("movement_penalty", 0)),
            stealth_penalty=int(value.get("stealth_penalty", 0)),
        )

    def _parse_food_component(
        self,
        value: object,
        file_path: Path,
        raw_id: str,
    ) -> FoodComponent | None:
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError(f"{file_path}: item {raw_id!r} [food] must be a table")

        if "nutrition" not in value:
            raise ValueError(f"{file_path}: item {raw_id!r} food component has no nutrition")

        return FoodComponent(
            nutrition=int(value["nutrition"]),
        )

    def _parse_charges_component(
        self,
        value: object,
        file_path: Path,
        raw_id: str,
    ) -> ChargesComponent | None:
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError(f"{file_path}: item {raw_id!r} [charges] must be a table")

        if "min_charges" not in value:
            raise ValueError(f"{file_path}: item {raw_id!r} charges component has no min_charges")

        if "max_charges" not in value:
            raise ValueError(f"{file_path}: item {raw_id!r} charges component has no max_charges")

        min_charges = int(value["min_charges"])
        max_charges = int(value["max_charges"])

        if min_charges < 0:
            raise ValueError(f"{file_path}: item {raw_id!r} min_charges must be >= 0")

        if max_charges < min_charges:
            raise ValueError(f"{file_path}: item {raw_id!r} max_charges must be >= min_charges")

        return ChargesComponent(
            min_charges=min_charges,
            max_charges=max_charges,
        )

    def _parse_identification_component(
        self,
        item: dict[str, Any],
        file_path: Path,
        raw_id: str,
    ) -> IdentificationComponent:
        raw_identification = item.get("identification")

        starts_identified = bool(item.get("starts_identified", True))
        appearance_group = item.get("appearance_group")

        if raw_identification is not None:
            if not isinstance(raw_identification, dict):
                raise ValueError(f"{file_path}: item {raw_id!r} [identification] must be a table")

            starts_identified = bool(raw_identification.get("starts_identified", starts_identified))
            appearance_group = raw_identification.get("appearance_group", appearance_group)

        if appearance_group is not None and not isinstance(appearance_group, str):
            raise ValueError(f"{file_path}: item {raw_id!r} appearance_group must be a string")

        return IdentificationComponent(
            starts_identified=starts_identified,
            appearance_group=appearance_group,
        )

    def _optional_str(self, value: object) -> str | None:
        if value is None:
            return None

        return str(value)
