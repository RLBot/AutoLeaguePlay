"""AutoLeague

Usage:
    autoleagueplay setup <working_dir>
    autoleagueplay run (odd | even | rolling) [--teamsize=T] [--replays=R] [--ignore-missing] [--autoshutdown=S] [--stale-rematch-threshold=X] [--half-robin]
    autoleagueplay bubble [--teamsize=T] [--replays=R]
    autoleagueplay list (odd | even | rolling) [--stale-rematch-threshold=X] [--half-robin]
    autoleagueplay results (odd | even | rolling)
    autoleagueplay check
    autoleagueplay test
    autoleagueplay fetch <season_num> <week_num>
    autoleagueplay leaderboard (odd | even | rolling) [--top-only]
    autoleagueplay leaderboard (clip | symbols | legend)
    autoleagueplay results-to-version-files <results_file>
    autoleagueplay unzip
    autoleagueplay (-h | --help)
    autoleagueplay --version

Options:
    --replays=R                  What to do with the replays of the match. Valid values are 'ignore', 'save', 'anonym' and 'calculated_gg'. [default: calculated_gg]
    --teamsize=T                 How many players per team. [default: 1]
    --ignore-missing             Allow the script to run even though not all bots are in the bot directory.
    --autoshutdown=S              Shutdown the system S seconds after autoleague ends, usefull for VMs. [default: 0]
    -h --help                    Show this screen.
    --version                    Show version.
    --stale-rematch-threshold=X  Skip matches when a bot has beaten another X times in a row, and neither of them have updated their code.
    --half-robin                 The divisions will be cut in half (with overlap) when setting up round-robins, for fewer matches.
    --top-only                   Only display top 40 bots on the leaderboard even though there might be more bots.
"""
import sys
from pathlib import Path

from docopt import docopt

from autoleagueplay.bubble_sort import run_bubble_sort
from autoleagueplay.ladder import RunStrategy
from autoleagueplay.leaderboard.leaderboard import (
    generate_leaderboard,
    generate_leaderboard_clip,
)
from autoleagueplay.leaderboard.symbols import generate_symbols, generate_legend
from autoleagueplay.list_matches import (
    list_matches,
    list_results,
    parse_results_and_write_files,
)
from autoleagueplay.load_bots import check_bot_folder, unzip_all_bots, DEFAULT_TIMESTAMP
from autoleagueplay.paths import WorkingDir
from autoleagueplay.replays import ReplayPreference
from autoleagueplay.run_matches import run_league_play
from autoleagueplay.settings import PersistentSettings
from autoleagueplay.sheets import fetch_ladder_from_sheets
from autoleagueplay.test_bots import test_all_bots
from autoleagueplay.version import __version__


def main():
    arguments = docopt(__doc__, version=__version__)
    settings = PersistentSettings.load()

    if arguments["setup"]:
        working_dir = Path(arguments["<working_dir>"])
        working_dir.mkdir(exist_ok=True, parents=True)
        WorkingDir(working_dir)  # Creates relevant directories and files
        settings.working_dir_raw = f"{working_dir}"
        settings.save()
        print(f"Working directory successfully set to '{working_dir}'")

    else:
        # Following commands require a working dir. Make sure it is set.
        if settings.working_dir_raw is None:
            print("No working directory set, use 'autoleagueplay setup <working_dir>'")
            sys.exit(0)

        working_dir = WorkingDir(Path(settings.working_dir_raw))

        stale_rematch_threshold = 0
        if arguments["--stale-rematch-threshold"]:
            stale_rematch_threshold = int(arguments["--stale-rematch-threshold"])

        run_strategy = None
        if arguments["odd"]:
            run_strategy = RunStrategy.ODD
        elif arguments["even"]:
            run_strategy = RunStrategy.EVEN
        elif arguments["rolling"]:
            run_strategy = RunStrategy.ROLLING

        half_robin = False
        if arguments["--half-robin"]:
            half_robin = True

        if arguments["leaderboard"]:
            if run_strategy is not None:
                generate_leaderboard(
                    working_dir, run_strategy, not arguments["--top-only"]
                )
            elif arguments["clip"]:
                generate_leaderboard_clip(working_dir)
            elif arguments["symbols"]:
                generate_symbols()
            elif arguments["legend"]:
                generate_legend(working_dir)
            else:
                raise NotImplementedError()

        elif arguments["run"]:

            replay_preference = ReplayPreference(arguments["--replays"])
            team_size = int(arguments["--teamsize"])
            shutdown_time = int(arguments["--autoshutdown"])

            if not arguments["--ignore-missing"]:
                all_present = check_bot_folder(working_dir, run_strategy)
                if all_present:
                    run_league_play(
                        working_dir,
                        run_strategy,
                        replay_preference,
                        team_size,
                        shutdown_time,
                        stale_rematch_threshold,
                        half_robin,
                    )
            else:
                run_league_play(
                    working_dir,
                    run_strategy,
                    replay_preference,
                    team_size,
                    shutdown_time,
                    stale_rematch_threshold,
                    half_robin,
                )

        elif arguments["bubble"]:

            replay_preference = ReplayPreference(arguments["--replays"])
            team_size = int(arguments["--teamsize"])

            run_bubble_sort(working_dir, team_size, replay_preference)

        elif arguments["list"]:
            list_matches(working_dir, run_strategy, stale_rematch_threshold, half_robin)

        elif arguments["results"]:
            list_results(working_dir, run_strategy, half_robin)

        elif arguments["check"]:
            check_bot_folder(working_dir)

        elif arguments["test"]:
            test_all_bots(working_dir)

        elif arguments["fetch"]:
            season = int(arguments["<season_num>"])
            week_num = int(arguments["<week_num>"])

            ladder = fetch_ladder_from_sheets(season, week_num)
            ladder.write(working_dir.ladder)

            print(
                f"Successfully fetched season {season} week {week_num} to '{working_dir.ladder}':"
            )
            for bot in ladder.bots:
                print(bot)

        elif arguments["results-to-version-files"]:
            results_file = arguments["<results_file>"]
            parse_results_and_write_files(
                working_dir, working_dir._working_dir / results_file, DEFAULT_TIMESTAMP
            )

        elif arguments["unzip"]:
            unzip_all_bots(working_dir)

        else:
            raise NotImplementedError()


if __name__ == "__main__":
    main()
