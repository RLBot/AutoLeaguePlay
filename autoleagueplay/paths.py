# -------------- STRUCTURE --------------
# ladder.txt   # Contains current ladder. Bot names separated by newlines.
# ladder_new.txt   # The ladder generated. Contains resulting ladder. Bot names separated by newlines.
# current_match.json    # Contains some information about the current match. Used by overlay scripts.
# bots/
#     skybot/..
#     botimus/..
#     ...
# results/
#     # This directory contains the match results. One json file for each match with all the info
#     quantum_bot1_vs_bot2_result.json
#     quantum_bot1_vs_bot3_result.json
#     ...
#

"""
This module contains file system paths that are used by autoleagueplay.
"""
from datetime import datetime
from pathlib import Path
from typing import Mapping, List

from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs

from autoleagueplay.ladder import Ladder
from autoleagueplay.match_history import MatchHistory
from autoleagueplay.versioned_bot import VersionedBot


class WorkingDir:
    """
    An object to make it convenient and safe to access file system paths within the working directory.
    """

    def __init__(self, working_dir: Path):
        self._working_dir = working_dir.absolute()
        self.ladder = self._working_dir / 'ladder.txt'
        self.new_ladder = self._working_dir / 'ladder_new.txt'
        self.match_results = self._working_dir / f'results'
        self.versioned_results = self._working_dir / f'versioned_results'
        self.bots = working_dir / 'bots'
        self.overlay_interface = working_dir / 'current_match.json'
        self.leaderboard = working_dir / 'leaderboard.png'
        self.leaderboard_clip = working_dir / 'leaderboard.mp4'
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        self.ladder.touch(exist_ok=True)
        self.match_results.mkdir(exist_ok=True)
        self.versioned_results.mkdir(exist_ok=True)
        self.bots.mkdir(exist_ok=True)

    def get_match_result(self, division_index: int, blue: str, orange: str) -> Path:
        match_name = f'{Ladder.DIVISION_NAMES[division_index].lower()}_{blue}_vs_{orange}.json'
        return self.match_results / match_name

    def get_version_specific_match_result(self, bot1: VersionedBot, bot2: VersionedBot) -> Path:
        return self._get_version_specific_match_result_from_keys(bot1.get_key(), bot2.get_key())

    def get_version_specific_match_result_from_times(
            self, name1: str, updated_date1: datetime, name2: str, updated_date2: datetime) -> Path:

        return self._get_version_specific_match_result_from_keys(
            VersionedBot.create_key(name1, updated_date1),
            VersionedBot.create_key(name2, updated_date2))

    def _get_version_specific_match_result_from_keys(self, key1: str, key2: str):
        match_name = MatchHistory.make_result_file_name(key1, key2, datetime.now())
        return self.versioned_results / match_name

    def get_version_specific_match_files(self, key1: str, key2: str) -> List[Path]:
        """
        Returns the match history between these two specific bot versions. The list of match results will be
        returned with the most recent match appearing first.
        """
        prefix = MatchHistory.make_result_file_prefix(key1, key2)
        files = list(self.versioned_results.glob(f'{prefix}*'))
        files.sort(reverse=True)
        return files

    def get_bots(self) -> Mapping[str, BotConfigBundle]:
        return {
            bot_config.name: bot_config
            for bot_config in scan_directory_for_bot_configs(self.bots)
        }


class PackageFiles:
    """
    An object to keep track of static paths that are part of this package
    """
    _package_dir = Path(__file__).absolute().parent
    default_match_config = _package_dir / 'default_match_config.cfg'

    _psyonix_bots = _package_dir / 'psyonix_bots'
    psyonix_allstar = _psyonix_bots / 'psyonix_allstar.cfg'
    psyonix_pro = _psyonix_bots / 'psyonix_pro.cfg'
    psyonix_rookie = _psyonix_bots / 'psyonix_rookie.cfg'
    psyonix_appearance = _psyonix_bots / 'psyonix_appearance.cfg'

    _cred = _package_dir / 'cred'
    sheets_token = _cred / 'sheets-api-token.pickle'
    credentials = _cred / 'credentials.json'
