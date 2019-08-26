from pywinauto.application import Application


def press_h():
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    win.type_keys("{h down}" "{h up}")

def press_9():
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window_(title_re='Rocket League.*')
    win.type_keys("{9 down}" "{9 up}")

