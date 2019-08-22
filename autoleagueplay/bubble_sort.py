import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from os.path import relpath
from time import sleep

from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs

from autoleagueplay.bubble_sort_overlay import BubbleSortOverlayData
from autoleagueplay.ladder import Ladder
from autoleagueplay.match_configurations import make_match_config
from autoleagueplay.match_result import MatchResult
from autoleagueplay.paths import WorkingDir
from autoleagueplay.replays import ReplayPreference
from autoleagueplay.run_matches import run_match
from autoleagueplay.versioned_bot import VersionedBot


@dataclass
class SortStepOutcome:
    upper_index: int
    sort_complete: bool


class BubbleSorter:

    def __init__(self, ladder: Ladder, working_dir: WorkingDir, team_size: int,
                 replay_preference: ReplayPreference):
        self.ladder = ladder
        self.working_dir = working_dir
        self.team_size = team_size
        self.replay_preference = replay_preference
        self.bundle_map = {}
        self.versioned_bots_by_name = {}
        self.num_already_played_during_iteration = 0

    def try_gather_versioned_bots(self):
        for i in range(3):
            try:
                self.gather_versioned_bots()
                return
            except Exception as e:
                print(e)
                sleep(1)

    def gather_versioned_bots(self):
        git_root = self.working_dir._working_dir

        subprocess.call(['git', 'pull'], cwd=git_root)

        bot_folders = [p for p in self.working_dir.bots.iterdir() if p.is_dir()]

        versioned_bots = set()

        for folder in bot_folders:
            relative_path = relpath(folder, git_root)
            iso_date_binary = subprocess.check_output(
                ["git", "log", "-n", "1", '--format="%ad"', "--date=iso-strict", "--", relative_path], cwd=git_root)
            iso_date = iso_date_binary.decode(sys.stdout.encoding).strip("\"\n")

            for bot_config in scan_directory_for_bot_configs(folder):
                versioned_bot = VersionedBot(bot_config, datetime.fromisoformat(iso_date))
                print(versioned_bot)
                versioned_bots.add(versioned_bot)

        self.bundle_map = {
            vb.get_unversioned_key(): vb.bot_config
            for vb in versioned_bots
        }
        self.versioned_bots_by_name = {
            vb.get_unversioned_key(): vb
            for vb in versioned_bots
        }

        bots_available = set([vb.get_unversioned_key() for vb in versioned_bots])
        incoming_bots = bots_available.difference(set(self.ladder.bots))
        self.ladder.bots.extend(incoming_bots)
        self.ladder.bots = [bot for bot in self.ladder.bots if bot in bots_available]

        self.ladder.write(self.working_dir.ladder)

    def begin(self):
        self.gather_versioned_bots()
        num_bots = len(self.ladder.bots)
        if num_bots < 2:
            raise Exception(f'Need at least 2 bots to run a bubble sort! Found {num_bots}')
        self.num_already_played_during_iteration = 0

        next_index = 0
        while True:
            step_outcome = self.advance(next_index)
            if step_outcome.sort_complete:
                break
            next_index = step_outcome.upper_index

        overlay_data = BubbleSortOverlayData(self.ladder.bots, self.versioned_bots_by_name, 0, False,
                                             self.working_dir._working_dir, winner=self.ladder.bots[0],
                                             sort_complete=True)
        overlay_data.write(self.working_dir.overlay_interface)

    def get_past_result(self, bot_1, bot_2) -> MatchResult:
        path = self.get_result_path(bot_1, bot_2)
        if path.exists():
            try:
                print(f'Found existing result {path.name}')
                return MatchResult.read(path)
            except Exception as e:
                print(f'Error loading result {path.name}. Fix/delete the result and run script again.')
                raise e
        return None

    def get_result_path(self, bot_1, bot_2):
        versioned_bot_1 = self.versioned_bots_by_name[bot_1]
        versioned_bot_2 = self.versioned_bots_by_name[bot_2]
        return self.working_dir.get_version_specific_match_result(versioned_bot_1, versioned_bot_2)

    def _on_match_complete(self, result):

        winner = result.winner.lower()
        loser = result.loser.lower()

        winner_index = self.ladder.bots.index(winner)
        loser_index = self.ladder.bots.index(loser)

        if winner_index > loser_index:
            # Need to swap the indices!
            self.ladder.bots[loser_index] = winner
            self.ladder.bots[winner_index] = loser

        self.ladder.write(self.working_dir.ladder)

    def advance(self, upper_index) -> SortStepOutcome:

        num_bots = len(self.ladder.bots)

        if upper_index == 0:
            # We've reached the top, time to jump back to the bottom (or decide we're done)
            if self.num_already_played_during_iteration == num_bots - 1:
                return SortStepOutcome(upper_index=upper_index, sort_complete=True)  # bubble sort is over!
            else:
                next_below = self.ladder.bots[num_bots - 1]
                next_above = self.ladder.bots[num_bots - 2]
                self.num_already_played_during_iteration = 0
                upper_index = num_bots - 2
        else:
            next_above = self.ladder.bots[upper_index - 1]
            next_below = self.ladder.bots[upper_index]
            upper_index -= 1

        past_result = self.get_past_result(next_above, next_below)

        if past_result is not None:
            self.num_already_played_during_iteration += 1
            overlay_data = BubbleSortOverlayData(self.ladder.bots, self.versioned_bots_by_name, upper_index, False,
                                                 self.working_dir._working_dir)
            overlay_data.write(self.working_dir.overlay_interface)
            self._on_match_complete(past_result)
            sleep(1)
            return SortStepOutcome(upper_index=upper_index, sort_complete=False)
        else:
            overlay_data = BubbleSortOverlayData(self.ladder.bots, self.versioned_bots_by_name, upper_index, True,
                                                 self.working_dir._working_dir)
            overlay_data.write(self.working_dir.overlay_interface)

            match_config = make_match_config(self.bundle_map[next_below], self.bundle_map[next_above], self.team_size)
            match_result = run_match(next_below, next_above, match_config, self.replay_preference)

            match_result.write(self.get_result_path(next_below, next_above))
            overlay_data = BubbleSortOverlayData(self.ladder.bots, self.versioned_bots_by_name, upper_index, True,
                                                 self.working_dir._working_dir, winner=match_result.winner.lower())
            overlay_data.write(self.working_dir.overlay_interface)

            self._on_match_complete(match_result)
            sleep(12)
            return SortStepOutcome(upper_index=upper_index, sort_complete=False)


def run_bubble_sort(working_dir: WorkingDir, team_size: int, replay_preference: ReplayPreference):

    # Ladder is a list of name.lower()
    ladder = Ladder.read(working_dir.ladder)

    sorter = BubbleSorter(ladder, working_dir, team_size, replay_preference)
    sorter.begin()
    print('Bubble sort is complete!')
    time.sleep(10)  # Leave some time to display the overlay.
