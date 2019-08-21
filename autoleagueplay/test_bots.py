import time
from dataclasses import dataclass
from typing import Optional

from rlbottraining.exercise_runner import run_playlist

from autoleagueplay.load_bots import load_all_bots
from autoleagueplay.match_exercise import MatchExercise

from autoleagueplay.run_matches import make_match_config

from autoleagueplay.ladder import Ladder

from autoleagueplay.paths import WorkingDir
from rlbot.training.training import Fail, Grade, Pass
from rlbottraining.grading.grader import Grader
from rlbottraining.grading.training_tick_packet import TrainingTickPacket


class FailDueToNoMovement(Fail):
    def __init__(self, bot: str, other_bot: str = None):
        self.bot = bot
        self.other_bot = other_bot

    def __repr__(self):
        if self.other_bot is not None:
            return f'FAIL: Both {self.bot} AND {self.other_bot} did not move during test match.'
        else:
            return f'FAIL: {self.bot} did not move during test match.'


@dataclass
class AliveGrader(Grader):

    first_packet_time: float = None
    test_total_time: float = 20
    test_min_time: float = 3

    blue_first_loc_y = None
    orange_first_loc_y = None

    blue_moved: bool = False
    orange_moved: bool = False

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:
        packet = tick.game_tick_packet
        if self.first_packet_time is None:
            self.first_packet_time = time.time()
            self.blue_first_loc_y = packet.game_cars[0].physics.location.y
            self.orange_first_loc_y = packet.game_cars[1].physics.location.y
        else:
            # Compare y location to check if bots have moved
            blue_new_loc_y = packet.game_cars[0].physics.location.y
            self.blue_moved = self.blue_moved or abs(self.blue_first_loc_y - blue_new_loc_y) > 5
            orange_new_loc_y = packet.game_cars[1].physics.location.y
            self.orange_moved = self.orange_moved or abs(self.orange_first_loc_y - orange_new_loc_y) > 5

        # Both bots have moved!
        if time.time() - self.first_packet_time > self.test_min_time and self.blue_moved and self.orange_moved:
            return Pass()

        # Check if time is up. If so fail test
        if time.time() - self.first_packet_time > self.test_total_time:
            if not self.blue_moved and not self.orange_moved:
                return FailDueToNoMovement(packet.game_cars[0].name, packet.game_cars[1].name)
            if not self.blue_moved:
                return FailDueToNoMovement(packet.game_cars[0].name)
            else:
                return FailDueToNoMovement(packet.game_cars[1].name)

        return None


def test_all_bots(working_dir: WorkingDir):
    """
    Tests if all bots work by starting a series of matches and check if the bots move
    """

    ladder = Ladder.read(working_dir.ladder)
    bot_count = len(ladder.bots)
    bots = load_all_bots(working_dir)

    # Pair each bot for a match. If there's an odd amount of bots, the last bot plays against the first bot
    pairs = [(ladder.bots[i], ladder.bots[i + 1]) for i in range(bot_count // 2)]
    if bot_count % 2 == 1:
        pairs.append((ladder.bots[0], ladder.bots[-1]))

    # Prepare matches
    matches = []
    for match_participant_pair in pairs:
        match_config = make_match_config(working_dir, bots[match_participant_pair[0]], bots[match_participant_pair[1]])
        match = MatchExercise(
            name=f'{match_participant_pair[0]} vs {match_participant_pair[1]}',
            match_config=match_config,
            grader=AliveGrader()
        )
        matches.append(match)

    fails = []

    # Play all the test matches
    for exercise_result in run_playlist(matches):
        if isinstance(exercise_result.grade, Fail):
            fails.append(exercise_result.grade)

    time.sleep(2)

    # Print summary
    print(f'All test matches have been played ({len(matches)} in total). Summary:')
    if len(fails) == 0:
        print(f'All bots seem to work!')
    else:
        for fail in fails:
            print(fail)
