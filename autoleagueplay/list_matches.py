from autoleagueplay.generate_matches import get_playing_division_indices, generate_round_robin_matches
from autoleagueplay.ladder import Ladder
from autoleagueplay.match_result import MatchResult, CombinedScore
from autoleagueplay.paths import WorkingDir


def list_matches(working_dir: WorkingDir, odd_week: bool):
    """
    Prints all the matches that will be run this week.
    """

    ladder = Ladder.read(working_dir.ladder)
    playing_division_indices = get_playing_division_indices(ladder, odd_week)

    if len(ladder.bots) < 2:
        print(f'Not enough bots on the ladder to play any matches')
        return

    print(f'Matches to play:')

    # The divisions play in reverse order, but we don't print them that way.
    for div_index in playing_division_indices:
        print(f'--- {Ladder.DIVISION_NAMES[div_index]} division ---')

        rr_bots = ladder.round_robin_participants(div_index)
        rr_matches = generate_round_robin_matches(rr_bots)

        for match_participants in rr_matches:
            print(f'{match_participants[0]} vs {match_participants[1]}')


def list_results(working_dir: WorkingDir, odd_week: bool):
    ladder = Ladder.read(working_dir.ladder)
    playing_division_indices = get_playing_division_indices(ladder, odd_week)

    if len(ladder.bots) < 2:
        print(f'Not enough bots on the ladder to play any matches')
        return

    print(f'Matches to play:')

    # Print all the matches played
    # The divisions play in reverse order, but we don't print them that way.
    for div_index in playing_division_indices:
        print(f'--- {Ladder.DIVISION_NAMES[div_index]} division ---')

        rr_bots = ladder.round_robin_participants(div_index)
        rr_matches = generate_round_robin_matches(rr_bots)

        for match_participants in rr_matches:
            result_str = ''
            result_path = working_dir.get_match_result(div_index, match_participants[0], match_participants[1])
            if result_path.exists():
                result = MatchResult.read(result_path)
                result_str = f'  (result: {result.blue_goals}-{result.orange_goals})'
            print(f'{match_participants[0]} vs {match_participants[1]}{result_str}')

    print('')
    # Print a table with all the combined scores
    for div_index in playing_division_indices:
        rr_bots = ladder.round_robin_participants(div_index)
        rr_matches = generate_round_robin_matches(rr_bots)
        rr_results = []
        for match_participants in rr_matches:
            result_path = working_dir.get_match_result(div_index, match_participants[0], match_participants[1])
            if result_path.exists():
                rr_results.append(MatchResult.read(result_path))

        overall_scores = [CombinedScore.calc_score(bot, rr_results) for bot in rr_bots]
        sorted_overall_scores = sorted(overall_scores)[::-1]

        print(f'--------------------------------+------+----------+-------+-------+-------+-------+')
        print(f'{Ladder.DIVISION_NAMES[div_index]:<32}| Wins | GoalDiff | Goals | Shots | Saves | Score |')
        print(f'--------------------------------+------+----------+-------+-------+-------+-------+')
        for score in sorted_overall_scores:
            print(f'{score.bot:<32}|  {score.wins:>2}  |    {score.goal_diff:>4}  |  {score.goals:>3}  |  {score.shots:>3}  |  {score.saves:>3}  | {score.points:>5} |')

    print(f'--------------------------------+------+----------+-------+-------+-------+-------+')
