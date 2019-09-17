from datetime import datetime

from rlbot.parsing.bot_config_bundle import BotConfigBundle


class VersionedBot:
    def __init__(self, bot_config: BotConfigBundle, updated_date: datetime):
        self.updated_date = updated_date
        self.bot_config = bot_config

    def __str__(self):
        return self.get_key()

    def get_key(self):
        return VersionedBot.create_key(self.get_unversioned_key(), self.updated_date)

    def get_unversioned_key(self):
        return self.bot_config.name

    @staticmethod
    def create_key(name: str, updated_date: datetime):
        return f'{name}-{updated_date.isoformat().replace(":", "-")}'
