import random
from typing import List, Tuple

from autoleagueplay.ladder import Ladder


def generate_round_robin_matches(bots: List[str]) -> List[Tuple[str, str]]:
    """
    Returns a list of pairs of bots that should play against each other for a round robin.
    """
    # This makes the list of matches consistent over multiple calls. E.g. the --list option will always so same order
    random.seed(bots[0] + bots[-1])

    # Create all possible pairs of bots with bots from the given list
    matches = []
    count = len(bots)
    for i in range(count):
        for j in range(i + 1, count):
            matches.append((bots[i], bots[j]))

    random.shuffle(matches)
    return matches


def get_playing_division_indices(ladder: Ladder, odd_week: bool) -> List[int]:
    # Result is a list containing either even or odd indices.
    # If there is only one division always play that division (division 0, quantum).
    return range(ladder.division_count())[int(odd_week) % 2::2] if ladder.division_count() > 1 else [0]
