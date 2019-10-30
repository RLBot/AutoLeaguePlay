import json
from datetime import timedelta
from pathlib import Path
from typing import List

from autoleagueplay.ladder import Ladder
from autoleagueplay.match_result import MatchResult
from autoleagueplay.versioned_bot import VersionedBot


def convert_match_result(match_result: MatchResult):
    return {
        "winner": match_result.winner,
        "loser": match_result.loser,
        "blue_goals": match_result.blue_goals,
        "orange_goals": match_result.orange_goals,
    }


class OverlayData:
    def __init__(
        self,
        division: int,
        blue_bot: VersionedBot,
        orange_bot: VersionedBot,
        ladder: Ladder,
        versioned_map,
        old_match_result: MatchResult,
        rr_bots: List[str],
        rr_results: List[MatchResult],
        message: str = "",
    ):
        self.division = division
        self.blue_config_path = (
            blue_bot.bot_config.config_path if blue_bot is not None else None
        )
        self.orange_config_path = (
            orange_bot.bot_config.config_path if orange_bot is not None else None
        )
        self.ladder = ladder.bots
        self.division_names = Ladder.DIVISION_NAMES[: ladder.division_count()]
        self.old_match_result = (
            {
                "winner": old_match_result.winner,
                "loser": old_match_result.loser,
                "blue_goals": old_match_result.blue_goals,
                "orange_goals": old_match_result.orange_goals,
            }
            if old_match_result is not None
            else None
        )
        self.division_bots = ladder.round_robin_participants(division)
        self.rr_bots = rr_bots
        self.rr_results = [convert_match_result(mr) for mr in rr_results]
        self.blue_name = blue_bot.bot_config.name if blue_bot is not None else ""
        self.orange_name = orange_bot.bot_config.name if orange_bot is not None else ""
        self.message = message

        self.bot_map = {}
        for bot in ladder.bots:
            self.bot_map[bot] = {
                "name": versioned_map[bot].bot_config.name,
                "updated_date": (
                    versioned_map[bot].updated_date + timedelta(seconds=0)
                ).timestamp(),
            }

    def write(self, path: Path):
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=4)
