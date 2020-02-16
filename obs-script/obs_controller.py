from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.logging_utils import get_logger
import time

import sys
from obswebsocket import obsws, requests

# Todo: add obs_settings.json to load port, password, host, and any other option. Ideally it would be in workplace and the path is sent as argument
#Todo: add check for existing scene, if not, create one with browser and gae record

class Observer():
    def __init__(self, ws):
        #self.game_interface = GameInterface(get_logger("observer"))
        #self.game_interface.load_interface()
        #self.game_interface.wait_until_loaded()
        self.main()

    def main(self):
        # this is only a proof of concept at this time
        while True:
            try:
                scenes = ws.call(requests.GetSceneList())
                for s in scenes.getScenes():
                    name = s['name']
                    print(u"Switching to {}".format(name))
                    ws.call(requests.SetCurrentScene(name))
                    time.sleep(2)

                print("End of list")

            except KeyboardInterrupt:
                pass

            time.sleep(0.1)

host = "localhost"
port = 4444
password = ''
ws = obsws(host, port, password)
ws.connect()

Observer(ws)

# ws.disconnect()