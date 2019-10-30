from datetime import datetime
from pathlib import Path
from typing import List, Dict

from autoleagueplay.match_result import MatchResult


class MatchHistory:

    def __init__(self, match_files: List[Path]):
        self.match_files = match_files
        self.match_files.sort(reverse=True)
        self.results = [MatchResult.read(path) for path in self.match_files]

    def is_empty(self):
        return len(self.match_files) == 0

    def get_latest_result(self):
        if self.is_empty():
            return None
        return self.results[0]

    def get_win_counts(self, games_to_check: int) -> Dict[str, int]:

        if self.is_empty():
            return None

        blue = self.results[0].blue
        orange = self.results[0].orange

        wins = dict()
        wins[blue] = 0
        wins[orange] = 0

        num_games = 0
        for match_result in self.results:
            num_games += 1
            if num_games > games_to_check:
                break
            if match_result.winner == blue:
                wins[blue] += 1
            elif match_result.winner == orange:
                wins[orange] += 1
            else:
                raise Exception(f'Unexpected bot name {match_result.winner} when analyzing history.')
        return wins

    def get_current_streak_length(self):

        latest_winner = self.get_latest_result().winner

        streak = 0
        for match_result in self.results:
            if match_result.winner != latest_winner:
                break
            streak += 1
        return streak

    @staticmethod
    def make_result_file_prefix(versioned_bot_key_1: str, versioned_bot_key_2: str):
        bot_keys = [versioned_bot_key_1, versioned_bot_key_2]
        bot_keys.sort()
        return f'{bot_keys[0]}_vs_{bot_keys[1]}'

    @staticmethod
    def make_result_file_name(versioned_bot_key_1: str, versioned_bot_key_2: str, time: datetime):
        prefix = MatchHistory.make_result_file_prefix(versioned_bot_key_1, versioned_bot_key_2)
        return f'{prefix}_at_{time.isoformat().replace(":", "-")}.json'
