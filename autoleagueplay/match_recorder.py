import subprocess
import signal
import os

from autoleagueplay.paths import WorkingDir, PackageFiles

class Recorder:
    def __init__(self, division, participants, working_dir: WorkingDir):
        self.output_file = f'[{division}] {participants[0]} vs {participants[1]}.mkv'
        self.output_file_path = working_dir.match_recordings / self.output_file
    
    def start(self):
        self.process = subprocess.Popen(
            f'{str(PackageFiles.ffmpeg_bin)} -f gdigrab -draw_mouse 0 -framerate 60 -i title="Rocket League (32-bit, DX9, Cooked)" -f dshow -i audio="virtual-audio-capturer" -c:v h264_nvenc -b:v 16000k "{self.output_file_path}" -y',
            stdout=subprocess.PIPE
        )
        print(f'ffmpeg recoding started... pid: {self.process.pid}')
    
    def stop(self):
        print(f'ffmpeg recoding stopped... killing pid: {self.process.pid}')
        os.kill(self.process.pid, signal.SIGTERM)
