from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip

from autoleagueplay.ladder import ladder_differences, Ladder, RunStrategy
from autoleagueplay.leaderboard.leaderboard_paths import LeaderboardPaths
from autoleagueplay.leaderboard.symbols import Symbols
from autoleagueplay.paths import WorkingDir


def generate_leaderboard(working_dir: WorkingDir, run_strategy: RunStrategy, extra: bool=False, background: bool=True):
    """
    Created a leaderboard that shows differences between the old ladder and the new ladder.
    :param working_dir: The working directory
    :param run_strategy: The strategy for running the ladder that was used this week.
    :param extra: Whether to include the next 5 divisions.
    :param background: Whether to use a background for the leaderboard.
    :param make_clip: Whether to also make an mp4 clip.
    :param duration: Duration of the clip in seconds.
    :param frames_per_second: frames per second of the clip.
    """

    assert working_dir.ladder.exists(), f'\'{working_dir.ladder}\' does not exist.'

    if not working_dir.new_ladder.exists():
        print(f'The new ladder has not been determined yet.')
        return

    old_ladder = Ladder.read(working_dir.ladder)
    new_ladder = Ladder.read(working_dir.new_ladder)

    new_bots, moved_up, moved_down = ladder_differences(old_ladder, new_ladder)
    played = old_ladder.all_playing_bots(run_strategy)

    # ---------------------------------------------------------------

    # PARAMETERS FOR DRAWING:

    # Divisions. We only have color palettes configured for a certain number of them, so enforce a limit.
    divisions = Ladder.DIVISION_NAMES[:len(Symbols.palette)]

    '''
    Each division has the origin at the top left corner of their emblem.

    Offsets:
        title offsets determine where the division title is drawn relative to the emblem.
        bot offsets determine where bot names are drawn relative to the emblem.
        sym offsets determine where the symbol is placed relative to the bot name.

    Increments:
        div increments are how much to move the origin between each division.
        bot increment is how much to move down for each bot name.

    '''

    # Start positions for drawing.
    start_x = 0
    start_y = 0

    # Division emblem offsets from the division name position.
    title_x_offset = 350
    title_y_offset = 85

    # Bot name offsets from the division name position.
    bot_x_offset = 200
    bot_y_offset = 300

    # Offsets for the symbols from the bot name position.
    sym_x_offset = 1295
    sym_y_offset = 5

    # Incremenets for x and y.
    div_x_incr = 1790
    div_y_incr = 790
    bot_y_incr = 140

    # ---------------------------------------------------------------

    # DRAWING:

    # Opening image for drawing.
    if background:
        if extra:
            leaderboard = Image.open(LeaderboardPaths.leaderboard_extra_empty)
        else:
            leaderboard = Image.open(LeaderboardPaths.leaderboard_empty)
    else:
        if extra:
            leaderboard = Image.open(LeaderboardPaths.leaderboard_extra_no_background)
        else:
            leaderboard = Image.open(LeaderboardPaths.leaderboard_no_background)

    draw = ImageDraw.Draw(leaderboard)

    # Fonts for division titles and bot names.
    div_font = ImageFont.truetype(str(LeaderboardPaths.font_medium), 120)
    bot_font = ImageFont.truetype(str(LeaderboardPaths.font_medium), 80)

    # Bot name colour.
    bot_colour = (0, 0, 0)

    # For each divion, draw the division name, and each bot in the division.
    for i, div in enumerate(divisions):

        # Calculates position for the division.
        div_pos = (start_x + div_x_incr * (i // 5), start_y + div_y_incr * (i % 5))

        # Draws the division emblem.
        try:
            # Opens the division emblem image.
            emblem = Image.open(LeaderboardPaths.emblems / f'{div}.png')
            # Pastes emblem onto image.
            leaderboard.paste(emblem, div_pos, emblem)
        except:
            # Sends warning message if it can't find the emblem.
            print(f'WARNING: Missing emblem for {div}.')

        # Draws the division title at an offset.
        title_pos = (div_pos[0] + title_x_offset, div_pos[1] + title_y_offset)
        draw.text(xy=title_pos, text=div, fill=Symbols.palette[div][0], font=div_font)

        # Loops through the four bots in the division and draws each.
        for ii, bot in enumerate(new_ladder.division(i)):

            # Calculates position for the bot name and draws it.
            bot_pos = (div_pos[0] + bot_x_offset, div_pos[1] + bot_y_offset + ii * bot_y_incr)
            draw.text(xy=bot_pos, text=bot, fill=bot_colour, font=bot_font)

            # Calculates symbol position.
            sym_pos = (bot_pos[0] + sym_x_offset, bot_pos[1] + sym_y_offset)

            # Pastes appropriate symbol
            if bot in new_bots:
                symbol = Image.open(LeaderboardPaths.symbols / f'{div}_new.png')
                leaderboard.paste(symbol, sym_pos, symbol)

            elif bot in moved_up:
                symbol = Image.open(LeaderboardPaths.symbols / f'{div}_up.png')
                leaderboard.paste(symbol, sym_pos, symbol)

            elif bot in moved_down:
                symbol = Image.open(LeaderboardPaths.symbols / f'{div}_down.png')
                leaderboard.paste(symbol, sym_pos, symbol)

            elif bot in played:
                symbol = Image.open(LeaderboardPaths.symbols / f'{div}_played.png')
                leaderboard.paste(symbol, sym_pos, symbol)

    # Saves the image.
    leaderboard.save(working_dir.leaderboard, 'PNG')

    print('Successfully generated leaderboard.')


def generate_leaderboard_clip(working_dir: WorkingDir, duration: float=5.0, frames_per_second: int=60):
    if working_dir.leaderboard.exists():
        clip = ImageClip(str(working_dir.leaderboard)).set_duration(duration)
        clip.write_videofile(str(working_dir.leaderboard_clip), fps=frames_per_second)
        print('Successfully generated leaderboard clip.')

    else:
        print(f'No leaderboard has been generated yet.')
