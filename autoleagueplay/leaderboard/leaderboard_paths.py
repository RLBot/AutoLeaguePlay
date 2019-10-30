from pathlib import Path


class LeaderboardPaths:
    """
    An object to keep track of paths to the leaderboard resources
    """

    _leaderboard_dir = Path(__file__).absolute().parent

    emblems = _leaderboard_dir / "emblems"
    symbols = _leaderboard_dir / "symbols"
    templates = _leaderboard_dir / "templates"

    leaderboard_extra_empty = templates / "Leaderboard_extra_empty.png"
    leaderboard_empty = templates / "Leaderboard_empty.png"
    leaderboard_extra_no_background = templates / "Leaderboard_extra_no_background.png"
    leaderboard_no_background = templates / "Leaderboard_no_background.png"

    font_regular = _leaderboard_dir / "MontserratAlternates-Regular.ttf"
    font_medium = _leaderboard_dir / "MontserratAlternates-Medium.ttf"
    font_bold = _leaderboard_dir / "MontserratAlternates-Bold.ttf"
