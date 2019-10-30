import time
from dataclasses import dataclass, field
from typing import Optional

from rlbot.setup_manager import SetupManager
from rlbot.training.training import Grade, Pass, Fail
from rlbot.utils.game_state_util import GameState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface
from rlbottraining.grading.grader import Grader
from rlbottraining.grading.training_tick_packet import TrainingTickPacket
from rlbottraining.rng import SeededRandomNumberGenerator
from rlbottraining.training_exercise import TrainingExercise

from autoleagueplay.match_result import MatchResult
from autoleagueplay.replays import ReplayPreference, ReplayMonitor
from autoleagueplay.key_macros import (
    hide_hud_macro,
    do_director_spectating_macro,
    hide_rendering_macro,
    show_percentages_macro,
    end_game_macro,
)


@dataclass
class MercyRule:

    required_goal_diff: int = 7
    game_interface: GameInterface = None

    mercy_detected: bool = False
    game_ended: bool = False

    def check_for_mercy(self, packet: GameTickPacket):
        blue_score = packet.teams[0].score
        orange_score = packet.teams[1].score

        # The mercy is detected as soon as the goal is scored. We want to watch the replay of the goal so
        # the match is terminated once we see the following kickoff
        if (
            abs(blue_score - orange_score) >= self.required_goal_diff
            and not self.mercy_detected
        ):
            self.que_save_replay()
            self.mercy_detected = True
        elif (
            not self.game_ended
            and packet.game_info.is_kickoff_pause
            and self.mercy_detected
        ):
            self.game_ended = True
            end_game_macro(True)

    def que_save_replay(self):
        game_state = GameState(console_commands=["QueSaveReplay"])
        self.game_interface.set_game_state(game_state)


class FailDueToNoReplay(Fail):
    def __repr__(self):
        return "FAIL: Match finished but no replay was written to disk."


@dataclass
class MatchGrader(Grader):

    mercy_rule: MercyRule = field(default_factory=MercyRule)
    replay_monitor: ReplayMonitor = field(default_factory=ReplayMonitor)

    last_match_time: float = 0
    last_game_tick_packet: GameTickPacket = None
    match_result: Optional[MatchResult] = None
    saw_active_packets = False

    has_pressed_h = False

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:
        if not self.has_pressed_h:
            hide_hud_macro()
            do_director_spectating_macro()
            show_percentages_macro()
            hide_rendering_macro()
            self.has_pressed_h = True

        self.replay_monitor.ensure_monitoring()

        # Check for mercy rule
        self.mercy_rule.check_for_mercy(tick.game_tick_packet)
        if self.mercy_rule.game_ended:
            self.match_result = fetch_match_score(tick.game_tick_packet)
            time.sleep(
                1
            )  # Give time for replay_monitor to register replay and for RL to load main menu
            if (
                self.replay_monitor.replay_id
                or self.replay_monitor.replay_preference
                == ReplayPreference.IGNORE_REPLAY
            ):
                self.replay_monitor.stop_monitoring()
                self.replay_monitor.anonymize_replay()
                return Pass()

        # Check if game is over and replay recorded
        self.last_game_tick_packet = tick.game_tick_packet
        game_info = tick.game_tick_packet.game_info
        if game_info.is_match_ended and self.saw_active_packets:
            self.match_result = fetch_match_score(tick.game_tick_packet)
            if (
                self.replay_monitor.replay_id
                or self.replay_monitor.replay_preference
                == ReplayPreference.IGNORE_REPLAY
            ):
                self.replay_monitor.stop_monitoring()
                self.replay_monitor.anonymize_replay()
                return Pass()
            seconds_since_game_end = game_info.seconds_elapsed - self.last_match_time
            if seconds_since_game_end > 15:
                self.replay_monitor.stop_monitoring()
                self.replay_monitor.anonymize_replay()
                return FailDueToNoReplay()
        else:
            if game_info.is_round_active and not game_info.is_match_ended:
                self.saw_active_packets = True
            self.last_match_time = game_info.seconds_elapsed
            return None


def fetch_match_score(packet: GameTickPacket):
    blue = packet.game_cars[0]
    orange = packet.game_cars[1]
    return MatchResult(
        blue=blue.name,
        orange=orange.name,
        blue_goals=packet.teams[0].score,
        orange_goals=packet.teams[1].score,
        blue_shots=blue.score_info.shots,
        orange_shots=orange.score_info.shots,
        blue_saves=blue.score_info.saves,
        orange_saves=orange.score_info.saves,
        blue_points=blue.score_info.score,
        orange_points=orange.score_info.score,
    )


@dataclass
class MatchExercise(TrainingExercise):

    grader: Grader = field(default_factory=MatchGrader)

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        return GameState()  # don't need to change anything
