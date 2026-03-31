import json
import pkgutil
from typing import TYPE_CHECKING, Dict, Iterable, NamedTuple

from . import Options

if TYPE_CHECKING:
    from . import CoQWorld

class CoQQuestData(NamedTuple):
    name: str
    region: str
    level: int

class CoQGoalData(NamedTuple):
    quest_step: str
    progression: int

# Order of keys in this .json is meaningful. Any quests in line after the goal quest will
# not be added to the multiworld.
quest_data = pkgutil.get_data(__name__, "data/Quests.json")
assert quest_data is not None
quest_locations: Dict[str, CoQQuestData] = {
    name: CoQQuestData(
        name=name,
        region=quest["region"] if "region" in quest else "Joppa",
        level=quest["level"] if "level" in quest else 1,
    )
    for name, quest in json.loads(quest_data).items()
}

# Quests that are options for the victory condition
goal_lookup: Dict[int, CoQGoalData] = {
    Options.Goal.option_quest_weirdwire_conduit: CoQGoalData(
        quest_step="Weirdwire Conduit... Eureka!~Return to Argyve",
        progression=3,
    ),
    Options.Goal.option_quest_more_than_a_willing_spirit: CoQGoalData(
        quest_step="More Than a Willing Spirit~Return to Grit Gate",
        progression=5,
    ),
    Options.Goal.option_quest_decoding_the_signal: CoQGoalData(
        quest_step="Decoding the Signal~Return to Grit Gate",
        progression=7,
    ),
    Options.Goal.option_quest_the_earl_of_omonporch: CoQGoalData(
        quest_step="The Earl of Omonporch~Return to Grit Gate",
        progression=8,
    ),
    Options.Goal.option_quest_a_call_to_arms: CoQGoalData(
        quest_step="A Call to Arms~Defend Grit Gate",
        progression=8,
    ),
}

def quest_keys(world: "CoQWorld") -> Iterable[str]:
    for name in quest_locations.keys():
        yield name
        if name == goal_lookup[world.options.goal.value].quest_step:
            break

# Max level is last required quest level + some extra
def max_level(world: "CoQWorld") -> int:
    return (
        quest_locations[goal_lookup[world.options.goal.value].quest_step].level
        + world.options.extra_location_levels
    )
