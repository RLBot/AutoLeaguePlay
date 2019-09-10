import os
import subprocess
import sys
from datetime import datetime
from os.path import relpath
from typing import Dict, Mapping, Optional
from zipfile import ZipFile

from rlbot.parsing.bot_config_bundle import get_bot_config_bundle, BotConfigBundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs

from autoleagueplay.ladder import Ladder
from autoleagueplay.paths import PackageFiles, WorkingDir
from autoleagueplay.versioned_bot import VersionedBot

# Maps Psyonix bots to their skill value. Initialized in load_all_bots()
psyonix_bots: Dict[str, float] = dict()


def load_all_bots(working_dir: WorkingDir) -> Mapping[str, BotConfigBundle]:
    bots = dict(working_dir.get_bots())

    # Psyonix bots
    psyonix_allstar = get_bot_config_bundle(PackageFiles.psyonix_allstar)
    psyonix_pro = get_bot_config_bundle(PackageFiles.psyonix_pro)
    psyonix_rookie = get_bot_config_bundle(PackageFiles.psyonix_rookie)
    bots[psyonix_allstar.name] = psyonix_allstar
    bots[psyonix_pro.name] = psyonix_pro
    bots[psyonix_rookie.name] = psyonix_rookie
    # Skill values for later. This way the user can rename the Psyonix bots by changing the config files, but we still
    # have their correct skill
    psyonix_bots[psyonix_allstar.name] = 1.0
    psyonix_bots[psyonix_pro.name] = 0.5
    psyonix_bots[psyonix_rookie.name] = 0.0

    return bots


def check_bot_folder(working_dir: WorkingDir, odd_week: Optional[bool]=None) -> bool:
    """
    Prints all bots missing from the bot folder.
    If odd_week is not None, it will filter for bots needed for the given type of week.
    Returns True if everything is okay and no bots are missing.
    """
    bots = load_all_bots(working_dir)
    ladder = Ladder.read(working_dir.ladder)
    needed_bots = ladder.all_playing_bots(odd_week) if odd_week is not None else ladder.bots
    none_missing = True
    for bot in needed_bots:
        if bot not in bots.keys():
            print(f'{bot} is missing from the bot folder.')
            none_missing = False
    if none_missing:
        print('No needed bots are missing from the bot folder.')
        return True
    return False


def load_all_bots_versioned(working_dir: WorkingDir) -> Mapping[str, VersionedBot]:

    bot_folders = [p for p in working_dir.bots.iterdir() if p.is_dir()]
    root = working_dir._working_dir
    versioned_bots = set()

    for folder in bot_folders:
        relative_path = relpath(folder, root)

        date = None
        try:
            iso_date_binary = subprocess.check_output(
                ["git", "log", "-n", "1", '--format="%ad"', "--date=iso-strict", "--", relative_path], cwd=root)
            iso_date = iso_date_binary.decode(sys.stdout.encoding).strip("\"\n")

            if len(iso_date) > 0:
                date = datetime.fromisoformat(iso_date)
        except Exception:
            pass

        if date is None:
            date = get_modified_date(folder)

        for bot_config in scan_directory_for_bot_configs(folder):
            versioned_bot = VersionedBot(bot_config, date)
            versioned_bots.add(versioned_bot)

    return {
        vb.get_unversioned_key(): vb
        for vb in versioned_bots
    }


def get_modified_date(folder) -> datetime:
    ignored_directories = ['__pycache__', '.git']
    ignored_files = ['RLBot_Core_Interface.dll']
    max_timestamp = 0
    for root, dirs, files in os.walk(folder, topdown=True):
        dirs[:] = [d for d in dirs if d not in ignored_directories]
        times = [os.stat(os.path.join(root, f)).st_mtime for f in files if f not in ignored_files]
        if len(times) > 0:
            timestamp = max(times)
            if timestamp > max_timestamp:
                max_timestamp = timestamp

    return datetime.fromtimestamp(max_timestamp)


def unzip_all_bots(working_dir: WorkingDir):
    for root, dirs, files in os.walk(working_dir._working_dir, topdown=True):
        dirs[:] = [d for d in dirs]
        for file in files:
            if '.zip' in file:
                path = os.path.join(root, file)
                if is_already_unzipped(path):
                    print(f'Skipping {path} because it has already been extracted.')
                    continue
                with ZipFile(path, 'r') as zipObj:
                    # Extract all the contents of zip file in current directory
                    print(f'Extracting {path}')
                    zipObj.extractall(path=root)

                    # https://stackoverflow.com/questions/9813243/extract-files-from-zip-file-and-retain-mod-date
                    for zip_info in zipObj.infolist():
                        extracted_path = os.path.join(root, zip_info.filename)
                        time_from_zip = datetime(*zip_info.date_time[0:6])
                        seconds = int(time_from_zip.timestamp())
                        os.utime(extracted_path, (seconds, seconds))


def is_already_unzipped(zipfile):
    with ZipFile(zipfile, 'r') as zipObj:
        for zip_info in zipObj.infolist():
            extracted_path = os.path.join(os.path.dirname(zipfile), zip_info.filename)
            if os.path.isfile(extracted_path):
                # Looks like this zip has already been extracted.
                return True
    return False
