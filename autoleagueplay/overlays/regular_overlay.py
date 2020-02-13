import os
import time
from threading import Thread
import webbrowser

import eel
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QFileDialog
from pip._internal import main as pipmain
from rlbot.utils import rate_limiter
from rlbot.utils import rate_limiter
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.structures import game_data_struct
import json
from datetime import datetime

game_tick_packet = None
should_quit = False


class GameTickReader:
    def __init__(self):
        self.logger = get_logger('packet reader')
        self.game_interface = GameInterface(self.logger)
        self.game_interface.load_interface()
        self.game_tick_packet = game_data_struct.GameTickPacket()

        #self.rate_limit = rate_limiter.RateLimiter(GAME_TICK_PACKET_REFRESHES_PER_SECOND)
        self.last_call_real_time = datetime.now()  # When we last called the Agent

    def get_packet(self):
        now = datetime.now()
        #self.rate_limit.acquire()
        self.last_call_real_time = now

        self.pull_data_from_game()
        return self.game_tick_packet

    def pull_data_from_game(self):
        self.game_interface.update_live_data_packet(self.game_tick_packet)


def as_jsonifyable(obj):
    if isinstance(obj, (int, float, str)):
        return obj
    elif "Array" in obj.__class__.__name__:
        return list(map(as_jsonifyable, obj))
    else:
        return {attr: as_jsonifyable(getattr(obj, attr)) for attr in dir(obj) if not attr.startswith("_")}


@eel.expose
def get_game_tick_packet():
    return as_jsonifyable(game_tick_packet)



def on_websocket_close(page, sockets):
    global should_quit
    eel.sleep(3.0)  # We might have just refreshed. Give the websocket a moment to reconnect.
    if not len(eel._websockets):
        # At this point we think the browser window has been closed.
        should_quit = True


def start():
    eel.init('')

    packet_reader = GameTickReader()

    eel.start('regular_overlay.html', callback=on_websocket_close, disable_cache=True)

    def reload_packet():
        while True:
            global game_tick_packet
            game_tick_packet = packet_reader.get_packet()
            time.sleep(1 / 120)

    th = Thread(target=reload_packet)
    th.start()

    while not should_quit:
        eel.sleep(1.0)

    th.join()

if __name__ == "__main__":
    start()
