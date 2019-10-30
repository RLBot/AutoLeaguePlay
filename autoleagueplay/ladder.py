import math
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Mapping


class RunStrategy(Enum):
    EVEN = 1
    ODD = 2
    ROLLING = 3


class Ladder:
    DIVISION_NAMES = (
        "Quantum",
        "Overclocked",
        "Processor",
        "Circuit",
        "Transistor",
        "Abacus",
        "Babbage",
        "Colossus",
        "Dragon",
        "ENIAC",
        "Ferranti",
        "Grundy",
        "Hobbit",
        "Imagination",
        "Jupiter",
        "Komputer",
        "Lambda",
    )

    def __init__(self, bots: List[str], division_size: int = 4, overlap_size: int = 1):
        self.bots = bots
        self.division_size = division_size
        self.overlap_size = overlap_size
        self.round_robin_size = division_size + overlap_size

    def division(self, division_index: int) -> List[str]:
        """
        Returns a list of bots in the division. Division at index 0 is Quantum, division at index 1 is Overclock, etc.
        """
        return self.bots[
            division_index
            * self.division_size : (1 + division_index)
            * self.division_size
        ]

    def division_count(self) -> int:
        return math.ceil(len(self.bots) / self.division_size)

    def round_robin_participants(self, division_index: int) -> List[str]:
        """
        Returns a list of bots participating in the round robin based on division index. Division at index 0 is Quantum,
        division at index 1 is Overclock, etc.
        """
        return self.bots[
            division_index
            * self.division_size : (1 + division_index)
            * self.division_size
            + self.overlap_size
        ]

    def playing_division_indices(self, run_strategy: RunStrategy) -> range:
        """
        Resulting list contains either even or odd indices. However, if there is only one division, that division will
         always (division 0, quantum).
        """
        if self.division_count() <= 1:
            return range(self.division_count())
        if run_strategy == RunStrategy.EVEN:
            return range(0, self.division_count(), 2)
        if run_strategy == RunStrategy.ODD:
            return range(1, self.division_count(), 2)
        if run_strategy == RunStrategy.ROLLING:
            return range(self.division_count())

    def all_playing_bots(self, run_strategy: RunStrategy) -> List[str]:
        """
        Returns a list of all bots that will play.
        """
        if run_strategy == RunStrategy.ROLLING:
            return self.bots.copy()
        playing = []
        playing_division_indices = self.playing_division_indices(run_strategy)
        for div_index in playing_division_indices:
            playing += self.round_robin_participants(div_index)
        return playing

    def write(self, path: Path):
        with open(path, "w") as f:
            for bot in self.bots:
                f.write(f"{bot}\n")

    @staticmethod
    def read(path: Path, division_size: int = 4) -> "Ladder":
        if not path.is_file():
            raise ValueError("Provided path is not a file.")
        with open(path, "r") as f:
            return Ladder([line.strip() for line in f], division_size)


def ladder_differences(
    old_ladder: Ladder, new_ladder: Ladder
) -> Tuple[List[str], Mapping[str, int]]:
    """
    Returns a list of new bots and a dictionary with bot movements on the ladder. If a bot moved up the number in
    the dictionary will be positive, if it moved down, it will be negative.
    """

    new_bots = []
    ranks_moved = {}

    for bot in new_ladder.bots:
        if bot not in old_ladder.bots:
            new_bots.append(bot)
        else:
            # Finds out how much the bot moved. Positive numbers means it moved up and negative numbers means down
            ranks_moved[bot] = old_ladder.bots.index(bot) - new_ladder.bots.index(bot)

    return new_bots, ranks_moved
