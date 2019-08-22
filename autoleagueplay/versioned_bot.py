from datetime import datetime

from rlbot.parsing.bot_config_bundle import BotConfigBundle


class VersionedBot:
    def __init__(self, bot_config: BotConfigBundle, updated_date: datetime):
        self.updated_date = updated_date
        self.bot_config = bot_config

    def __str__(self):
        return self.get_key()

    def get_key(self):
        return f'{self.get_unversioned_key()}-{self.updated_date.isoformat().replace(":", "-")}'

    def get_unversioned_key(self):
        return self.bot_config.name.lower()
