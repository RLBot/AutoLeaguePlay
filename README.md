# AutoLeague for League Play
[DomNomNom's Autoleague](https://github.com/DomNomNom/AutoLeague) modified to play [RLBot](http://rlbot.org/)'s Official League Play.

# How to use:

Recommended: Use [Bakkesmod](https://bakkesmod.com/) and have 'Automatically save all replays' enabled.

Installation:
- To install, clone this repo and run `pip install -e .` in the directory containing `setup.py`.
- This should give you access to the `autoleagueplay` command line tool. Try `autoleagueplay --help`.
- Run the `autoleagueplay setup <working_dir>` command to set the directory where you want your league to be stored.

Usage:
```
autoleagueplay setup <working_dir>                           | Setup a league directory. Required for some other commands.
autoleagueplay run (odd | even | rolling) 
                                [--teamsize=T] 
                                [--replays=R]
                                [--ignore-missing]
                                [--autoshutdown=S]          
                                [--stale-rematch-threshold=X]
                                [--half-robin]               | Runs a league play event.
autoleagueplay bubble [--teamsize=T] [--replays=R]           | Runs a bubble sort.
autoleagueplay list (odd | even | rolling)    
                                [--stale-rematch-threshold=X]
                                [--half-robin]               | Lists all matches for the next odd or even week.
autoleagueplay results (odd | even | rolling)                | Lists the results.
autoleagueplay fetch <season_num> <week_num>                 | Fetches the given ladder from the Google Sheets.
autoleagueplay check                                         | Checks if all bots are present in the bot folder.
autoleagueplay test                                          | Test run all bots to see if they auto-start
autoleagueplay leaderboard (odd | even | rolling) [--extra]  | Generate a leaderboard image.
autoleagueplay leaderboard (clip | symbols | legend)         | Generate a clip or legend for the leaderboard, or update symbols.
autoleagueplay results-to-version-files <results_file>       | Generates match result files by parsing the output of the results command.
autoleagueplay unzip                                         | Unzips all the zip files in the bot folder.
autoleagueplay (-h | --help)                                 | Show commands and options.
autoleagueplay --version                                     | Show version.
```

Options:
```
-h --help                    Show this screen.
--version                    Show version.
--replays=R                  What to do with the replays of the match. Valid values are 'save', and 'calculated_gg'. [default: calculated_gg]
--list                       Instead of playing the matches, the list of matches is printed.
--results                    Like --list but also shows the result of matches that has been played.
--ignore-missing             Allow the script to run even though not all bots are in the bot directory.
--skip-stale-rematches       Skip matches when the same versions of both bots have already played each other.
--stale-rematch-threshold=X  Skip matches when a bot has beaten another X times in a row, and neither of them have updated their code.
--half-robin                 The divisions will be cut in half (with overlap) when setting up round-robins, for fewer matches.
--top-only                   Only display top 40 bots on the leaderboard even though there might be more bots.
```

The working directory contains:
- `ladder.txt`. This contains the bot names separated by newlines (it can be copy-pasted directly from the sheet, or fetched with the fetch command).
- `bots/`. Directory containing the bots and their files.
- `results/`. Directory containing results. Each match will get a json file with all the relevant data, and they are named something like `quantum_reliefbot_vs_atlas_result.json`.
- `versioned_results/`. Directory containing a result tagged with the specific code versions of the bots participating.

When running the script use `odd` or `even` or `rolling` as argument to set what type of week it should play:
- Odd: Overclocked, Circuit, Transitor, ect plays.
- Even: Quantum, Processor, Abacus, etc plays.
- Rolling: Play all divisions, starting at the bottom and moving upward toward Quantum.
If a bot keeps winning, it can move up multiple divisions as we roll through.

Special options:
- Stale rematch threshold:
  - The threshold is an integer. 
  - If a pair of bots have played at least stale-rematch-threshold matches under their current version, and one of 
    the bots won all of the stale-rematch-threshold most recent matches, future matches get skipped.
- Half-robin:
  - For each division, play a lower RR and an upper RR, with overlap.
  - 3 bots on the bottom play 3 games, the winner advances and is included when the 3 bots on the top play 3 games.
  - This results in fewer games, at the cost of less diversity in who you face.

When all results are found, a new ladder `ladder_new.txt` is created next to the original ladder file.

### Advanced Usage:

#### Match Config
Change `autoleague/default_match_config.cfg` for other game modes and mutators.

#### Psyonix Bots
AutoLeaguePlay can handle Psyonix bots, but their names must be: `Psyonix Allstar`, `Psyonix Pro`, and `Psyonix Rookie`.
You don't have to give them config files in the `bots/` directory. AutoLeaguePlay has its own config files for Psyonix bots.
If you really want to give them different names, change them [there](https://github.com/NicEastvillage/AutoLeague/blob/master/autoleagueplay/psyonix_allstar.cfg).

#### Fetching ladder from Google Sheets
You can fetch the ladder from the Google Sheets with the `autopleagueplay fetch <season_num> <week_num>` command.
Before you can use this you must get a `credentials.json` file which you can get by enabling [Google Sheets API](https://developers.google.com/sheets/api/quickstart/python) and then download the client configurations.
Put the `credentials.json ` in `autopleagueplay/cred/`. Next time you run the command, Google wants your permission, and then it should work.

#### Current Match and Overlay
AutoLeaguePlay creates a `current_match.json` in the working directory whenever a match is about to begin.
This file contains the division, and the paths to the bots currently playing. E.g.:

```json
{
    "division": 0,
    "blue_config_path": "C:\\User\\RLBot\\League\\bots\\Self-driving car\\self-driving-car.cfg",
    "orange_config_path": "C:\\User\\RLBot\\League\\bots\\Beast from the East\\beastbot.cfg"
}
```

The information in the file can be used for an overlay.
When the new ladder is complete the `current_match.json` is removed.
