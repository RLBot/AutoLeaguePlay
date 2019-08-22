import random
from pathlib import Path

from rlbot.matchconfig.conversions import read_match_config_from_file
from rlbot.matchconfig.match_config import MatchConfig, Team, PlayerConfig
from rlbot.parsing.bot_config_bundle import BotConfigBundle

from autoleagueplay.load_bots import psyonix_bots
from autoleagueplay.paths import PackageFiles


def make_match_config(blue: BotConfigBundle, orange: BotConfigBundle, team_size: int=1,
                      config_location=PackageFiles.default_match_config) -> MatchConfig:

    match_config = read_match_config_from_file(config_location)
    match_config.game_map = random.choice([
        'ChampionsField',
        'Farmstead',
        'DFHStadium',
        'Wasteland',
        'BeckwithPark'
    ])
    player_configs = []

    for i in range(0, team_size):
        player_configs.append(make_bot_config(blue, Team.BLUE))
        player_configs.append(make_bot_config(orange, Team.ORANGE))

    match_config.player_configs = player_configs

    return match_config


def make_bot_config(config_bundle: BotConfigBundle, team: Team) -> PlayerConfig:
    # Our main concern here is Psyonix bots
    player_config = PlayerConfig.bot_config(Path(config_bundle.config_path), team)
    player_config.rlbot_controlled = player_config.name not in psyonix_bots.keys()
    player_config.bot_skill = psyonix_bots.get(player_config.name, 1.0)
    return player_config
