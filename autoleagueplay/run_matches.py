import time

from rlbot.setup_manager import setup_manager_context
from rlbot.training.training import Fail
from rlbot.utils.logging_utils import get_logger
from rlbottraining.exercise_runner import run_playlist, RenderPolicy

from autoleagueplay.generate_matches import generate_round_robin_matches
from autoleagueplay.ladder import Ladder
from autoleagueplay.load_bots import load_all_bots_versioned
from autoleagueplay.match_configurations import make_match_config
from autoleagueplay.match_exercise import MatchExercise, MatchGrader, MercyRule
from autoleagueplay.match_result import CombinedScore, MatchResult
from autoleagueplay.overlay import OverlayData
from autoleagueplay.paths import WorkingDir
from autoleagueplay.replays import ReplayPreference, ReplayMonitor

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
        for exercise_result in run_playlist([match], setup_manager=setup_manager, render_policy=RenderPolicy.NO_TRAINING_RENDER):

            # Warn users if no replay was found
            if isinstance(exercise_result.grade, Fail) and exercise_result.exercise.grader.replay_monitor.replay_id == None:
                print(f'WARNING: No replay was found for the match \'{participant_1} vs {participant_2}\'. Is Bakkesmod injected and \'Automatically save all replays\' enabled?')

            return exercise_result.exercise.grader.match_result


def run_league_play(working_dir: WorkingDir, odd_week: bool, replay_preference: ReplayPreference, team_size: int,
                    shutdowntime: int, skip_stale_rematches: bool):
    """
    Run a league play event by running round robins for half the divisions. When done, a new ladder file is created.
    """

    bots = load_all_bots_versioned(working_dir)
    ladder = Ladder.read(working_dir.ladder)

    # We need the result of every match to create the next ladder. For each match in each round robin, if a result
    # exist already, it will be parsed, if it doesn't exist, it will be played.
    # When all results have been found, the new ladder can be completed and saved.
    new_ladder = Ladder(ladder.bots)
    event_results = []

    # playing_division_indices contains either even or odd indices.
    # If there is only one division always play that division (division 0, quantum).
    playing_division_indices = range(ladder.division_count())[int(odd_week) % 2::2] if ladder.division_count() > 1 else [0]

    # The divisions play in reverse order, so quantum/overclocked division plays last
    for div_index in playing_division_indices[::-1]:
        print(f'Starting round robin for the {Ladder.DIVISION_NAMES[div_index]} division')

        rr_bots = ladder.round_robin_participants(div_index)
        rr_matches = generate_round_robin_matches(rr_bots)
        rr_results = []

        for match_participants in rr_matches:

            versioned_result_path = working_dir.get_version_specific_match_result(
                bots[match_participants[0]], bots[match_participants[1]])

            # Check if match has already been play, i.e. the result file already exist
            result_path = working_dir.get_match_result(div_index, match_participants[0], match_participants[1])

            if skip_stale_rematches and versioned_result_path.exists():
                path_to_use = versioned_result_path
            else:
                path_to_use = result_path

            if path_to_use.exists():
                # Found existing result
                try:
                    print(f'Found existing result {path_to_use.name}')
                    result = MatchResult.read(path_to_use)

                    rr_results.append(result)

                except Exception as e:
                    print(f'Error loading result {path_to_use.name}. Fix/delete the result and run script again.')
                    raise e

            else:
                # Let overlay know which match we are about to start
                overlay_data = OverlayData(
                    div_index,
                    bots[match_participants[0]].bot_config.config_path,
                    bots[match_participants[1]].bot_config.config_path)

                overlay_data.write(working_dir.overlay_interface)

                participant_1 = bots[match_participants[0]]
                participant_2 = bots[match_participants[1]]
                match_config = make_match_config(participant_1.bot_config, participant_2.bot_config, team_size)
                result = run_match(participant_1.bot_config.name, participant_2.bot_config.name, match_config,
                                   replay_preference)
                result.write(result_path)
                result.write(versioned_result_path)
                print(f'Match finished {result.blue_goals}-{result.orange_goals}. Saved result as {result_path}'
                      f' and also {versioned_result_path}')

                rr_results.append(result)

                # Let the winner celebrate and the scoreboard show for a few seconds.
                # This sleep not required.
                time.sleep(8)

        print(f'{Ladder.DIVISION_NAMES[div_index]} division done')
        event_results.append(rr_results)

        # Find bots' overall score for the round robin
        overall_scores = [CombinedScore.calc_score(bot, rr_results) for bot in rr_bots]
        sorted_overall_scores = sorted(overall_scores)[::-1]
        print(f'Bots\' overall performance in {Ladder.DIVISION_NAMES[div_index]} division:')
        for score in sorted_overall_scores:
            print(f'> {score.bot:<32}: wins={score.wins:>2}, goal_diff={score.goal_diff:>3}, goals={score.goals:>2}, shots={score.shots:>2}, saves={score.saves:>2}, points={score.points:>2}')

        # Rearrange bots in division on the new ladder
        first_bot_index = new_ladder.division_size * div_index
        bots_to_rearrange = len(rr_bots)
        for i in range(bots_to_rearrange):
            new_ladder.bots[first_bot_index + i] = sorted_overall_scores[i].bot

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
