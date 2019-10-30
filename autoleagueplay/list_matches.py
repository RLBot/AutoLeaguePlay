import re
from datetime import datetime
from pathlib import Path
from typing import List

from autoleagueplay.generate_matches import generate_round_robin_matches
from autoleagueplay.ladder import Ladder, RunStrategy
from autoleagueplay.load_bots import load_all_bots_versioned
from autoleagueplay.match_result import MatchResult, CombinedScore
from autoleagueplay.paths import WorkingDir
from autoleagueplay.run_matches import get_round_robin_ranges, get_stale_match_result


def list_matches(
    working_dir: WorkingDir,
    run_strategy: RunStrategy,
    stale_rematch_threshold: int = 0,
    half_robin: bool = False,
):
    """
    Prints all the matches that will be run this week.

    :param stale_rematch_threshold: If a bot has won this number of matches in a row against a particular opponent
    and neither have had their code updated, we will consider it to be a stale rematch and skip future matches.
    If 0 is passed, we will not skip anything.
    :param half_robin: If true, we will split the division into an upper and lower round-robin, which reduces the
    number of matches required.
    """

    ladder = Ladder.read(working_dir.ladder)
    playing_division_indices = ladder.playing_division_indices(run_strategy)
    bots = load_all_bots_versioned(working_dir)

    if len(ladder.bots) < 2:
        print(f"Not enough bots on the ladder to play any matches")
        return

    print(f"Matches to play:")

    num_matches = 0
    num_skipped = 0

    # The divisions play in reverse order.
    for div_index in playing_division_indices[::-1]:
        division_name = (
            Ladder.DIVISION_NAMES[div_index]
            if div_index < len(Ladder.DIVISION_NAMES)
            else div_index
        )
        print(f"--- {division_name} division ---")

        round_robin_ranges = get_round_robin_ranges(ladder, div_index, half_robin)

        for start_index, end_index in round_robin_ranges:
            rr_bots = ladder.bots[start_index : end_index + 1]
            rr_matches = generate_round_robin_matches(rr_bots)

            for match_participants in rr_matches:
                bot1 = bots[match_participants[0]]
                bot2 = bots[match_participants[1]]
                stale_match_result = get_stale_match_result(
                    bot1, bot2, stale_rematch_threshold, working_dir
                )
                if stale_match_result is not None:
                    num_skipped += 1
                    continue

                num_matches += 1
                print(f"{match_participants[0]} vs {match_participants[1]}")

    print(f"Matches to run: {num_matches}  Matches skipped: {num_skipped}")


def list_results(working_dir: WorkingDir, run_strategy: RunStrategy, half_robin: bool):
    ladder = Ladder.read(working_dir.ladder)
    playing_division_indices = ladder.playing_division_indices(run_strategy)

    if len(ladder.bots) < 2:
        print(f"Not enough bots on the ladder to play any matches")
        return

    # Write overview to file first, then print content of the file
    with open(working_dir.results_overview, "w") as f:
        f.write(f"Matches:\n")

        if run_strategy == RunStrategy.ROLLING or half_robin:
            # The ladder was dynamic, so we can't print divisions neatly.
            # Just print everything in one blob.
            match_results = [
                MatchResult.read(path) for path in working_dir.match_results.glob("*")
            ]
            for result in match_results:
                result_str = f"  (result: {result.blue_goals}-{result.orange_goals})"
                f.write(f"{result.blue} vs {result.orange}{result_str}\n")

            write_overall_scores(f, ladder.bots, match_results)

        else:
            # The divisions play in reverse order, but we don't print them that way.
            for div_index in playing_division_indices:
                f.write(f"--- {Ladder.DIVISION_NAMES[div_index]} division ---\n")

                rr_bots = ladder.round_robin_participants(div_index)
                rr_matches = generate_round_robin_matches(rr_bots)

                for match_participants in rr_matches:
                    result_str = ""
                    result_path = working_dir.get_match_result(
                        div_index, match_participants[0], match_participants[1]
                    )
                    if result_path.exists():
                        result = MatchResult.read(result_path)
                        result_str = (
                            f"  (result: {result.blue_goals}-{result.orange_goals})"
                        )
                    f.write(
                        f"{match_participants[0]} vs {match_participants[1]}{result_str}\n"
                    )

            f.write("\n")

            # Print a table with all the combined scores
            for div_index in playing_division_indices:
                rr_bots = ladder.round_robin_participants(div_index)
                rr_matches = generate_round_robin_matches(rr_bots)
                rr_results = []
                for match_participants in rr_matches:
                    result_path = working_dir.get_match_result(
                        div_index, match_participants[0], match_participants[1]
                    )
                    if result_path.exists():
                        rr_results.append(MatchResult.read(result_path))

                write_overall_scores(f, rr_bots, rr_results, div_index)

            f.write(
                f"--------------------------------+------+----------+-------+-------+-------+-------+\n"
            )

    # Results have been writen to the file, now display the content
    with open(working_dir.results_overview, "r") as f:
        print(f.read())

    print(f"Result overview was written to '{working_dir.results_overview}'")


def write_overall_scores(
    file, rr_bots: List[str], rr_results: List[MatchResult], div_index: int = -1
):
    """
    Write a header and list of overall results in a table. Specifically, the table contains all the given bots' overall
    results based on the given list of results. If the div_index is set to a negative number, the header will
    display 'All bots', otherwise it will be the name of the division.
    """
    overall_scores = [CombinedScore.calc_score(bot, rr_results) for bot in rr_bots]
    sorted_overall_scores = sorted(overall_scores)[::-1]
    division_name = Ladder.DIVISION_NAMES[div_index] if div_index >= 0 else "All Bots"
    file.write(
        f"--------------------------------+------+----------+-------+-------+-------+-------+\n"
    )
    file.write(
        f"{division_name:<32}| Wins | GoalDiff | Goals | Shots | Saves | Score |\n"
    )
    file.write(
        f"--------------------------------+------+----------+-------+-------+-------+-------+\n"
    )
    for score in sorted_overall_scores:
        file.write(
            f"{score.bot:<32}|  {score.wins:>2}  |    {score.goal_diff:>4}  |  {score.goals:>3}  |  {score.shots:>3}  |  {score.saves:>3}  | {score.points:>5} |\n"
        )


def parse_results(filename):
    """
    If you have the output of the list_results function as a text document, you can use this function to parse it
    out into MatchResult objects. This is a slightly hacky utility function for manual use.
    """
    with open(filename) as f:
        line_list = f.readlines()

    vs_lines = [line for line in line_list if " vs " in line]

    results = []

    for line in vs_lines:
        m = re.search(r"(.+) vs (.+)  \(result: ([0-9]+)-([0-9]+)\)", line)
        if m is not None:
            result = MatchResult(
                blue=m.group(1),
                orange=m.group(2),
                blue_goals=int(m.group(3)),
                orange_goals=int(m.group(4)),
                blue_shots=0,
                orange_shots=0,
                blue_saves=0,
                orange_saves=0,
                blue_points=0,
                orange_points=0,
            )

            results.append(result)

    return results


def parse_results_and_write_files(
    working_dir: WorkingDir, results_file: Path, fallback_time: datetime
):
    """
    If you have the output of the list_results function as a text document, you can use this function to parse it
    out into MatchResult objects, and write those results with versioned file names. If a bot cannot be found in the
    working_dir, we will use the fallback_time when generating the versioned file name.
    """
    results = parse_results(working_dir._working_dir / results_file)
    bots = load_all_bots_versioned(working_dir)
    for result in results:

        blue_time = fallback_time
        if result.blue in bots:
            blue_time = bots[result.blue].updated_date

        orange_time = fallback_time
        if result.orange in bots:
            orange_time = bots[result.orange].updated_date

        result_path = working_dir.get_version_specific_match_result_from_times(
            result.blue, blue_time, result.orange, orange_time
        )

        print(f"Writing result to {result_path}")
        result.write(result_path)
