import os
import time
from threading import Thread
import webbrowser
from obswebsocket import obsws, requests


import eel
from rlbot.setup_manager import SetupManager
from rlbot.utils.structures.game_data_struct import GameTickPacket

game_tick_packet = None
should_quit = False
FPS = 120

class GameTickReader:
    def __init__(self):
        self.manager = SetupManager()
        self.manager.connect_to_game()
        self.game_interface = self.manager.game_interface

    def get_packet(self):
        packet = GameTickPacket()
        return self.game_interface.update_live_data_packet(packet)


def as_jsonifyable(obj):
    if isinstance(obj, (int, float, str)):
        return obj
    elif "Array" in obj.__class__.__name__:
        return list(map(as_jsonifyable, obj))
    else:
        return {attr: as_jsonifyable(getattr(obj, attr)) for attr in dir(obj) if not attr.startswith("_")}


@eel.expose
def get_game_tick_packet():
    global game_tick_packet
    return as_jsonifyable(game_tick_packet)



def on_websocket_close(page, sockets):
    global should_quit
    eel.sleep(20.0)  # We might have just refreshed. Give the websocket a moment to reconnect.
    if not len(eel._websockets):
        # At this point we think the browser window has been closed.
        should_quit = True
        print("DEAD")


# @eel.expose
def start():
    packet_reader = GameTickReader()
    global should_quit

    def reload_packet():
        game_ended = False
        #Todo: Refresh obs webpage
        #Todo: start obs recording
        #Todo: check if obs is running, otherwise this wont run

        host = "localhost"
        port = 4444
        password = ''
        ws = obsws(host, port, password)
        ws.connect()

        recording = False

        while not game_ended:
            global game_tick_packet
            game_tick_packet = packet_reader.get_packet()
            # time.sleep(1)
            time.sleep(1/120)
            game_ended = game_tick_packet.game_info.is_match_ended
            print(game_ended)

            if not recording:
                ws.call(requests.StartRecording())
                recording = True

        if game_ended:
            time.sleep(12)
            #Todo: shut down obs recording
            ws.call(requests.StopRecording())
            ws.disconnect()
            exit()


    th = Thread(target=reload_packet)
    th.start()

    eel.init('autoleagueplay/overlays')

    eel.start('regular_overlay.html', port=8002, mode=False, callback=on_websocket_close, disable_cache=True)


    while not should_quit:
        eel.sleep(1.0)



    th.join()
    exit()

if __name__ == "__main__":
    time.sleep(2)
    start()
