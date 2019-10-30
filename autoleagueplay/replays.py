from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any
import shutil
import os
import RattletrapPython.rattletrap as rat
import json

import requests
from rlbottraining.history.metric import Metric
from autoleagueplay.paths import WorkingDir
from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer

class ReplayPreference(Enum):
    SAVE = 'save'  # save to the default replays directory
    CALCULATED_GG = 'calculated_gg'  # save locally and upload to https://calculated.gg/
    IGNORE_REPLAY = 'ignore'
    ANONYMIZE_REPLAY = 'anonym'


def upload_to_calculated_gg(replay_path: Path):
    with open(replay_path, 'rb') as f:
        response = requests.post('https://calculated.gg/api/upload', files={'replays': f})
        print(f'upload response to {replay_path.name}: {response}')

def anonymize_replay(replay_path: Path, working_dir: WorkingDir):
    replay_name = str(os.path.basename(str(replay_path)).split('.')[0])
    anonym_replay_path = working_dir.replays / str(replay_name + '.replay')
    anonym_json_path = working_dir.replays / str('replay' + '.json')
    rat.parse(str(replay_path), anonym_json_path)

    with open(anonym_json_path) as replay_file:
        replay = json.load(replay_file)
    try:
        replay['header']['body']['properties']['value']['Team0Score']['value']['int'] = 0
    except:
        pass
    try:
        replay['header']['body']['properties']['value']['Team1Score']['value']['int'] = 0
    except:
        pass
    try:
        replay['header']['body']['properties']['value']['HighLights']['value']['array'] = []
    except:
        pass
    try:
        replay['header']['body']['properties']['value']['HighLights']['size'] = '0'
    except:
        pass
    try:
        replay['header']['body']['properties']['value']['Goals']['value']['array'] = []
    except:
        pass
    try:
        replay['header']['body']['properties']['value']['Goals']['size'] = '0'
    except:
        pass
    try:
        replay['content']['body']['marks'] = []
    except:
        pass
    with open(anonym_json_path, 'w') as replay_file:
        json.dump(replay, replay_file, indent=4)

    rat.generate(anonym_json_path, str(anonym_replay_path))




def parse_replay_id(replay_path: Path) -> str:
    replay_id, extension = replay_path.name.split('.')
    assert extension == 'replay'
    return replay_id


@dataclass
class ReplayMonitor(Metric):

    replay_preference: ReplayPreference
    working_dir: WorkingDir

    replay_id: str = None
    observer: Observer = None

    def to_json(self) -> Dict[str, Any]:
        return {
            'replay_id': self.replay_id,
        }

    def ensure_monitoring(self):
        if self.replay_preference == ReplayPreference.IGNORE_REPLAY or self.observer is not None:
            return
        replay_monitor = self
        class SetReplayId(LoggingEventHandler):
            def on_modified(set_replay_id_self, event):
                if event.is_directory: return
                assert event.src_path.endswith('.replay')
                nonlocal replay_monitor
                replay_path = Path(event.src_path)
                if replay_monitor.replay_preference == ReplayPreference.CALCULATED_GG:
                    upload_to_calculated_gg(replay_path)
                if replay_monitor.replay_preference == ReplayPreference.ANONYMIZE_REPLAY:
                    anonymize_replay(replay_path, replay_monitor.working_dir)
                replay_monitor.replay_id = parse_replay_id(replay_path)

            def on_created(set_replay_id_self, event):
                if event.is_directory: return
                assert event.src_path.endswith('.replay')
                nonlocal replay_monitor
                replay_path = Path(event.src_path)
                if replay_monitor.replay_preference == ReplayPreference.CALCULATED_GG:
                    upload_to_calculated_gg(replay_path)
                if replay_monitor.replay_preference == ReplayPreference.ANONYMIZE_REPLAY:
                    anonymize_replay(replay_path, replay_monitor.working_dir)
                replay_monitor.replay_id = parse_replay_id(replay_path)

            def on_deleted(self, event):
                pass
            def on_moved(self, event):
                pass

        self.observer = Observer()
        self.observer.daemon = True
        self.observer.schedule(SetReplayId(), str(get_replay_dir()), recursive=True)
        self.observer.start()

    def stop_monitoring(self):
        if self.observer is not None:
            self.observer.stop()
            self.observer.join(1)

    def anonymize_replay(self):
        pass

def get_replay_dir() -> Path:
    replay_dir = Path.home() / 'documents' / 'My Games' / 'Rocket League' / 'TAGame' / 'Demos'
    assert replay_dir.exists()
    return replay_dir