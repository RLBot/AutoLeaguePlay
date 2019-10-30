import time

from pywinauto.application import Application


def hide_hud_macro():
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    win.type_keys("{h down}" "{h up}")


def do_director_spectating_macro():
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    win.type_keys("{9 down}" "{9 up}")


def hide_rendering_macro():
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    win.type_keys("{PGDN down}" "{PGDN up}")


def show_percentages_macro():
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    win.type_keys("{HOME down}" "{HOME up}")


def end_game_macro(save_a_qued_replay: bool):
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    for cmd in ["{ESC}", "{VK_UP}", "{ENTER}", "{VK_LEFT}", "{ENTER}"]:
        win.type_keys(cmd)
        time.sleep(0.1)
    if save_a_qued_replay:
        win.type_keys("{ENTER}")
