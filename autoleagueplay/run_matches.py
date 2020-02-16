import time
from pathlib import Path
import threading
import os
from subprocess import call


from rlbot.setup_manager import setup_manager_context
from rlbot.training.training import Fail
from rlbot.utils.logging_utils import get_logger
from rlbottraining.exercise_runner import run_playlist, RenderPolicy

from autoleagueplay.generate_matches import generate_round_robin_matches
from autoleagueplay.ladder import Ladder, RunStrategy
from autoleagueplay.load_bots import load_all_bots_versioned
from autoleagueplay.match_configurations import make_match_config
from autoleagueplay.match_exercise import MatchExercise, MatchGrader, MercyRule
from autoleagueplay.match_history import MatchHistory
from autoleagueplay.match_result import CombinedScore, MatchResult
from autoleagueplay.overlay import OverlayData
from autoleagueplay.paths import WorkingDir
from autoleagueplay.replays import ReplayPreference, ReplayMonitor
from autoleagueplay.versioned_bot import VersionedBot

logger = get_logger('autoleagueplay')


def run_match(participant_1: str, participant_2: str, match_config, replay_preference: ReplayPreference) -> MatchResult:
    with setup_manager_context() as setup_manager:

        # Prepare the match exercise
        print(f'Starting match: {participant_1} vs {participant_2}. Waiting for match to finish...')
        match = MatchExercise(
            name=f'{participant_1} vs {participant_2}',
            match_config=match_config,
            grader=MatchGrader(
                mercy_rule=MercyRule(game_interface=setup_manager.game_interface),
                replay_monitor=ReplayMonitor(replay_preference=replay_preference),
            )
        )

        # If any bots have signed up for early start, give them 10 seconds.
        # This is typically enough for Scratch.
        setup_manager.early_start_seconds = 10



        # For loop, but should only run exactly once
        for exercise_result in run_playlist([match], setup_manager=setup_manager):

            # Warn users if no replay was found
            if isinstance(exercise_result.grade, Fail) and exercise_result.exercise.grader.replay_monitor.replay_id == None:
                print(f'WARNING: No replay was found for the match \'{participant_1} vs {participant_2}\'. Is Bakkesmod injected and \'Automatically save all replays\' enabled?')

            return exercise_result.exercise.grader.match_result


def run_league_play(working_dir: WorkingDir, run_strategy: RunStrategy, replay_preference: ReplayPreference,
                    team_size: int, shutdowntime: int, stale_rematch_threshold: int = 0, half_robin: bool = False):
    """
    Run a league play event by running round robins for half the divisions. When done, a new ladder file is created.

    :param stale_rematch_threshold: If a bot has won this number of matches in a row against a particular opponent
    and neither have had their code updated, we will consider it to be a stale rematch and skip future matches.
    If 0 is passed, we will not skip anything.
    :param half_robin: If true, we will split the division into an upper and lower round-robin, which reduces the
    number of matches required.
    """

    bots = load_all_bots_versioned(working_dir)
    ladder = Ladder.read(working_dir.ladder)

    latest_bots = [bot for bot in bots.values() if bot.bot_config.name in ladder.bots]
    latest_bots.sort(key=lambda b: b.updated_date, reverse=True)
    print('Most recently updated bots:')
    for bot in latest_bots:
        print(f'{bot.updated_date.isoformat()} {bot.bot_config.name}')

    # We need the result of every match to create the next ladder. For each match in each round robin, if a result
    # exist already, it will be parsed, if it doesn't exist, it will be played.
    # When all results have been found, the new ladder can be completed and saved.
    new_ladder = Ladder(ladder.bots)
    event_results = []

    # playing_division_indices contains either even or odd indices.
    # If there is only one division always play that division (division 0, quantum).
    playing_division_indices = ladder.playing_division_indices(run_strategy)

    # The divisions play in reverse order, so quantum/overclocked division plays last
    for div_index in playing_division_indices[::-1]:
        print(f'Starting round robin for the {Ladder.DIVISION_NAMES[div_index]} division')

        round_robin_ranges = get_round_robin_ranges(ladder, div_index, half_robin)

        for start_index, end_index in round_robin_ranges:
            rr_bots = ladder.bots[start_index:end_index + 1]
            rr_matches = generate_round_robin_matches(rr_bots)
            rr_results = []

            for match_participants in rr_matches:

                # Check if match has already been played during THIS session. Maybe something crashed and we had to
                # restart autoleague, but we want to pick up where we left off.
                session_result_path = working_dir.get_match_result(div_index, match_participants[0], match_participants[1])
                participant_1 = bots[match_participants[0]]
                participant_2 = bots[match_participants[1]]

                if session_result_path.exists():
                    print(f'Found existing result {session_result_path.name}')
                    rr_results.append(MatchResult.read(session_result_path))
                else:
                    historical_result = get_stale_match_result(participant_1, participant_2, stale_rematch_threshold,
                                                               working_dir, True)
                    if historical_result is not None:
                        rr_results.append(historical_result)
                        # Don't write to result files at all, since this match didn't actually occur.
                        overlay_data = OverlayData(div_index, participant_1, participant_2, new_ladder, bots,
                                                   historical_result, rr_bots, rr_results)
                        overlay_data.write(working_dir.overlay_interface)
                        time.sleep(8)  # Show the overlay for a while. Not needed for any other reason.

                    else:
                        # Let overlay know which match we are about to start
                        overlay_data = OverlayData(div_index, participant_1, participant_2, new_ladder, bots, None,
                                                   rr_bots, rr_results)

                        overlay_data.write(working_dir.overlay_interface)

                        match_config = make_match_config(participant_1.bot_config, participant_2.bot_config, team_size)

                        overlay_controller_path = os.path.join(os.path.dirname(__file__), './overlays/regular_overlay.py')

                        def overlay_controller_thread():
                            call(["python", overlay_controller_path])

                        controllerThread = threading.Thread(target=overlay_controller_thread)
                        controllerThread.start()

                        result = run_match(participant_1.bot_config.name, participant_2.bot_config.name, match_config,
                                           replay_preference)

                        result.write(session_result_path)
                        versioned_result_path = working_dir.get_version_specific_match_result(participant_1,
                                                                                              participant_2)
                        result.write(versioned_result_path)
                        print(f'Match finished {result.blue_goals}-{result.orange_goals}. Saved result as '
                              f'{session_result_path} and also {versioned_result_path}')

                        rr_results.append(result)

                        # Let the winner celebrate and the scoreboard show for a few seconds.
                        # This sleep not required.
                        time.sleep(8)

            # Find bots' overall score for the round robin
            overall_scores = [CombinedScore.calc_score(bot, rr_results) for bot in rr_bots]
            sorted_overall_scores = sorted(overall_scores)[::-1]
            division_result_message = f'Bots\' overall round-robin performance ({Ladder.DIVISION_NAMES[div_index]} division):\n'
            for score in sorted_overall_scores:
                division_result_message += f'> {score.bot:<32}: wins={score.wins:>2}, goal_diff={score.goal_diff:>3}\n'

            print(division_result_message)
            overlay_data = OverlayData(div_index, None, None, new_ladder, bots, None, rr_bots, rr_results,
                                       division_result_message)
            overlay_data.write(working_dir.overlay_interface)

            # Rearrange bots in division on the new ladder
            first_bot_index = start_index
            bots_to_rearrange = len(rr_bots)
            for i in range(bots_to_rearrange):
                new_ladder.bots[first_bot_index + i] = sorted_overall_scores[i].bot

            event_results.append(rr_results)

            time.sleep(8)  # Show the division overlay for a while.

        print(f'{Ladder.DIVISION_NAMES[div_index]} division done')

    # Save new ladder
    Ladder.write(new_ladder, working_dir.new_ladder)
    print(f'Done. Saved new ladder as {working_dir.new_ladder.name}')
    if shutdowntime != 0:
        import subprocess
        subprocess.call("shutdown.exe -s -t " + str(shutdowntime))

    # Remove overlay interface file now that we are done
    if working_dir.overlay_interface.exists():
        working_dir.overlay_interface.unlink()

    return new_ladder


def get_round_robin_ranges(ladder, div_index, half_robin):
    """
    Returns a list of tuples. Each tuple has the start index and the end index (inclusive) of some ladder slots
    that should participate in a round robin. For example, it might return [(4, 2), (2, 0)], which means there
    should be a round robin including slots 4, 3, 2, and another round robin including slots 2, 1, 0.
    :param ladder: The ladder we're playing in.
    :param div_index: The index of the division that is currently being played.
    :param half_robin: True if we want to split this division into two round-robins so fewer matches need to be played.
    """

    if half_robin:
        num_bots = ladder.division_size + ladder.overlap_size

        # smaller indices = higher bots on the ladder
        upper_range = (div_index * ladder.division_size, div_index * ladder.division_size + num_bots // 2)
        lower_range = (div_index * ladder.division_size + num_bots // 2, (div_index + 1) * ladder.division_size)
        sub_ranges = [lower_range, upper_range]
    else:
        sub_ranges = [(div_index * ladder.division_size, (div_index + 1) * ladder.division_size)]
    return sub_ranges


def find_historical_result(bot1: VersionedBot, bot2: VersionedBot, session_result_path: Path,
                           stale_rematch_threshold: int, working_dir: WorkingDir):
    if session_result_path.exists():
        # Found existing result
        try:
            print(f'Found existing result {session_result_path.name}')
            return MatchResult.read(session_result_path)

        except Exception as e:
            print(f'Error loading result {session_result_path.name}. Fix/delete the result and run script again.')
            raise e

    return get_stale_match_result(bot1, bot2, stale_rematch_threshold, working_dir, True)


def get_stale_match_result(bot1: VersionedBot, bot2: VersionedBot, stale_rematch_threshold: int,
                           working_dir: WorkingDir, print_debug: bool = False):
    if stale_rematch_threshold > 0:
        match_history = MatchHistory(working_dir.get_version_specific_match_files(bot1.get_key(), bot2.get_key()))
        if not match_history.is_empty():
            streak = match_history.get_current_streak_length()
            if streak >= stale_rematch_threshold:
                if print_debug:
                    print(f'Found stale rematch between {bot1.bot_config.name} and {bot2.bot_config.name}. '
                          f'{match_history.get_latest_result().winner} has won {streak} times in a row.')
                return match_history.get_latest_result()
    return None
