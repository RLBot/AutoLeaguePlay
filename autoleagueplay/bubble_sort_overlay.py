import json
from os.path import relpath
from pathlib import Path
from typing import List


class BubbleSortOverlayData:
    def __init__(self, ladder: List[str], versioned_map, sort_index: int, needs_match: bool, root_dir, winner: str=None,
                 sort_complete: bool=False):
        self.ladder = ladder
        self.bot_map = {}

        for bot in self.ladder:
            raw_logo = versioned_map[bot].bot_config.get_logo_file()
            logo = None
            if raw_logo is not None:
                logo = relpath(versioned_map[bot].bot_config.get_logo_file(), root_dir)
            self.bot_map[bot] = {
                'name': versioned_map[bot].bot_config.name,
                'logo': logo,
                'updated_date': versioned_map[bot].updated_date.timestamp(),
            }

        self.sort_index = sort_index
        self.needs_match = needs_match
        self.winner = winner
        self.sort_complete = sort_complete

    def write(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)
