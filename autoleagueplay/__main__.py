"""AutoLeague

Usage:
    autoleagueplay setup <working_dir>
    autoleagueplay run (odd | even) [--teamsize=T] [--replays=R] [--ignore-missing] [--autoshutdown=S] [--skip-stale-rematches]
    autoleagueplay bubble [--teamsize=T] [--replays=R]
    autoleagueplay list (odd | even)
    autoleagueplay results (odd | even)
    autoleagueplay check
    autoleagueplay test
    autoleagueplay fetch <season_num> <week_num>
    autoleagueplay leaderboard (odd | even)
    autoleagueplay leaderboard (clip | symbols | legend)
    autoleagueplay results-to-version-files <results_file>
    autoleagueplay unzip
    autoleagueplay (-h | --help)
    autoleagueplay --version

Options:
    --replays=R                  What to do with the replays of the match. Valid values are 'ignore', 'save', and 'calculated_gg'. [default: calculated_gg]
    --teamsize=T                 How many players per team. [default: 1]
    --ignore-missing             Allow the script to run even though not all bots are in the bot directory.
    --autoshutdown=S              Shutdown the system S seconds after autoleague ends, usefull for VMs. [default: 0]
    -h --help                    Show this screen.
    --version                    Show version.
    --skip-stale-rematches       Skip matches when the same versions of both bots have already played each other.
"""
import sys
from pathlib import Path

from docopt import docopt

from autoleagueplay.bubble_sort import run_bubble_sort
from autoleagueplay.leaderboard.leaderboard import generate_leaderboard, generate_leaderboard_clip
from autoleagueplay.leaderboard.symbols import generate_symbols, generate_legend
from autoleagueplay.list_matches import list_matches, list_results, parse_results_and_write_files
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

    if arguments['setup']:
        working_dir = Path(arguments['<working_dir>'])
        working_dir.mkdir(exist_ok=True, parents=True)
        WorkingDir(working_dir)   # Creates relevant directories and files
        settings.working_dir_raw = f'{working_dir}'
        settings.save()
        print(f'Working directory successfully set to \'{working_dir}\'')

    else:
        # Following commands require a working dir. Make sure it is set.
        if settings.working_dir_raw is None:
            print('No working directory set, use \'autoleagueplay setup <working_dir>\'')
            sys.exit(0)

        working_dir = WorkingDir(Path(settings.working_dir_raw))

        if arguments['leaderboard']:
            if arguments['odd'] or arguments['even']:
                generate_leaderboard(working_dir, arguments['odd'])
            elif arguments['clip']:
                generate_leaderboard_clip(working_dir)
            elif arguments['symbols']:
                generate_symbols()
            elif arguments['legend']:
                generate_legend(working_dir)
            else:
                raise NotImplementedError()

        elif arguments['run']:

            replay_preference = ReplayPreference(arguments['--replays'])
            team_size = int(arguments['--teamsize'])
            odd_week = arguments['odd']
            shutdown_time = int(arguments['--autoshutdown'])
            skip_stale = arguments['--skip-stale-rematches']

            if not arguments['--ignore-missing']:
                all_present = check_bot_folder(working_dir, odd_week)
                if all_present:
                    run_league_play(working_dir, odd_week, replay_preference, team_size, shutdown_time, skip_stale)
            else:
                run_league_play(working_dir, odd_week, replay_preference, team_size, shutdown_time, skip_stale)

        elif arguments['bubble']:

            replay_preference = ReplayPreference(arguments['--replays'])
            team_size = int(arguments['--teamsize'])

            run_bubble_sort(working_dir, team_size, replay_preference)

        elif arguments['list']:
            list_matches(working_dir, arguments['odd'])

        elif arguments['results']:
            list_results(working_dir, arguments['odd'])

        elif arguments['check']:
            check_bot_folder(working_dir)

        elif arguments['test']:
            test_all_bots(working_dir)

        elif arguments['fetch']:
            season = int(arguments['<season_num>'])
            week_num = int(arguments['<week_num>'])

            ladder = fetch_ladder_from_sheets(season, week_num)
            ladder.write(working_dir.ladder)

            print(f'Successfully fetched season {season} week {week_num} to \'{working_dir.ladder}\':')
            for bot in ladder.bots:
                print(bot)

        elif arguments['results-to-version-files']:
            results_file = arguments['<results_file>']
            parse_results_and_write_files(working_dir, working_dir._working_dir / results_file, DEFAULT_TIMESTAMP)

        elif arguments['unzip']:
            unzip_all_bots(working_dir)

        else:
            raise NotImplementedError()


if __name__ == '__main__':
    main()
