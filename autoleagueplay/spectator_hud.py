from pywinauto.application import Application


def press_h():
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    win.type_keys("{h down}" "{h up}")
