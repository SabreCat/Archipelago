import json
import pkgutil
from typing import TYPE_CHECKING, Dict, NamedTuple

from BaseClasses import LocationProgressType, Region

from . import Items, Locations, Quests

if TYPE_CHECKING:
    from . import CoQWorld

class CoQRegionData(NamedTuple):
    name: str
    parent: str
    unlock: str
    level_start: int
    level_end: int

region_data = pkgutil.get_data(__name__, "data/Regions.json")
assert region_data is not None
all_regions: Dict[str, CoQRegionData] = {
    name: CoQRegionData(
        name=name,
        parent=region["parent"],
        unlock=region["unlock"] if "unlock" in region else "",
        level_start=region["levelStart"] if "levelStart" in region else 0,
        level_end=region["levelEnd"] if "levelEnd" in region else 0,
    )
    for name, region in json.loads(region_data).items()
}

def add_level_locations(world: "CoQWorld", region: Region, start: int, end: int):
    for level in range(start, end):
        for loc_name in Locations.xp_locations(
            level, level + 1, world.options.locations_per_level
        ):
            if level > Quests.max_level(world): break
            level_loc = Locations.CoQLocation(
                world.player, loc_name, world.location_name_to_id[loc_name], region
            )
            level_loc.access_rule = lambda state, level=level: Items.has_enough_stats_for_level(
                level, state, world
            )
            level_loc.progress_type = LocationProgressType.DEFAULT
            region.locations += [level_loc]

def add_quests(world: "CoQWorld"):
    for quest_name in Quests.quest_keys(world):
        region = world.get_region(Quests.quest_locations[quest_name].region)

        if quest_name == Quests.goal_lookup[world.options.goal]:
            # Add victory event instead of normal location
            quest_loc = Locations.CoQLocation(world.player, quest_name, None, region)
            quest_loc.place_locked_item(
                Items.CoQItem(
                    "Victory", Items.ItemClassification.progression, None, world.player
                )
            )
        else:
            quest_loc = Locations.CoQLocation(
                world.player, quest_name, world.location_name_to_id[quest_name], region
            )
        quest_loc.access_rule = lambda state, quest_name=quest_name: Items.has_enough_stats_for_level(
            Quests.quest_locations[quest_name].level, state, world
        )
        quest_loc.progress_type = LocationProgressType.PRIORITY
        region.locations += [quest_loc]

def add_static_locations(world: "CoQWorld"):
    for quest in [
        k
        for k in Locations.static_locations.values()
        if k.type == "delivery" or k.type == "lore"
           or (k.type == "artifact" and world.options.lost_artifacts)
           and k.min_level <= Quests.max_level(world)
    ]:
        region = world.get_region(quest.region)
        quest_loc = Locations.CoQLocation(
            world.player, quest.name, world.location_name_to_id[quest.name], region
        )
        quest_loc.access_rule = lambda state, quest=quest: Items.has_enough_stats_for_level(
            quest.min_level, state, world
        )
        quest_loc.progress_type = LocationProgressType.PRIORITY if (quest.type == "lore"
            ) else LocationProgressType.DEFAULT
        region.locations += [quest_loc]

def create_regions(world: "CoQWorld"):
    # Default always-reachable region
    menu = Region("Menu", world.player, world.multiworld)
    world.multiworld.regions += [menu]

    # Qud regions, based around quests
    for region in all_regions.values():
        new_region = Region(region.name, world.player, world.multiworld)
        if region.level_start > 0 and region.level_end > 0:
            add_level_locations(world, new_region, region.level_start, region.level_end)
        world.multiworld.regions += [new_region]
        parent_region = world.get_region(region.parent)
        entrance_name = f"{parent_region.name} to {region.name}"
        if region.unlock and region.unlock != "":
            parent_region.connect(new_region, entrance_name, lambda state, region=region:
                                  state.has(region.unlock, world.player))
        else:
            parent_region.connect(new_region, entrance_name)
    
    add_quests(world)
    add_static_locations(world)
