import obspython as obs
import os
import time
from datetime import datetime
import psutil
import ctypes

from rlbot.utils import rate_limiter
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.structures import game_data_struct
import json
from rlbot.parsing.custom_config import ConfigObject
from rlbot.parsing.bot_config_bundle import BotConfigBundle, get_bot_config_bundle

import rlbot.parsing.custom_config as cc
SETUP = True

GAME_TICK_PACKET_REFRESHES_PER_SECOND = 120  # 2*60. https://en.wikipedia.org/wiki/Nyquist_rate


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

        ##########################################


source_name = ""
activated = False

def script_unload():
    global packet_reader

    try:
        packet_reader.game_interface.game
    except:
        print('Packet Reader does not Exist')
        return
    if packet_reader.game_interface.game is not None:
        dll = packet_reader.game_interface.game
        handle = dll._handle
        del dll
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.FreeLibrary.argtypes = [wintypes.HMODULE]
        success = kernel32.FreeLibrary(handle)
        print('Unloading status: ' + str(success))
        del packet_reader
        obs.timer_remove(frame_tick)


def frame_tick():
    global packet_reader
    global bot_num
    global elapsed
    global overtime
    global ended
    global kickoff
    global team
    global name
    global total_goals
    global own_goals
    global bot_list
    global goal_time
    global end_time
    global start_time
    global names
    global cheer
    global total_blue
    global total_orange
    global boost
    global boost_bar_pos
    global orange_name_item
    global blue_boost_item
    global ended

    boost_bar_pos = [10, 100]


    try:
        packet = packet_reader.get_packet()
    except:
        print("Can't read packet")
        return

    teams = [0, 1]
    # Todo: reset score after game
    if not league_on:
        league_info = league_status()
        if league_info is None:
            print('League has not started yet')
            return

    if time.time() >= end_time:
        print('STOP')
        obs.obs_frontend_recording_stop()
        end_time = 99999999999999999999999999999999999999
        buffer_delay = time.time() + 20
        return

    if packet.game_info.is_match_ended:
        boost = [[0, 0], [0, 0]]
        total_blue = 0
        total_orange = 0
        do_reset_bar()
        boost_bar(boost)
        set_names('Blue-Name', '')
        set_names('Orange-Name', '')
        prev_total_goals = 0
        if obs.obs_frontend_recording_active() and end_time == 99999999999999999999999999999999999999 and not ended:
            end_time = time.time() + end_delay
        ended = True
        return
    else:
        if not obs.obs_frontend_recording_active() and start_time == 99999999999999999999999999999999999999:
            #Todo: add start match delay around 3 seconds
            start_time = time.time() + 3
            ended = False
        if time.time() >= start_time:
            obs.obs_frontend_recording_start()
            start_time = 99999999999999999999999999999999999999
            ended = False
            return
    ended = False



    for n in range(bot_num):
        team = packet.game_cars[n].team
        name = packet.game_cars[n].name.lower()

        if team == 0:
            boost[0][0] = packet.game_cars[n].boost / 100
        else:
            boost[0][1] = packet.game_cars[n].boost/100

    prev_overtime = overtime
    prev_ended = ended
    prev_total_goals = total_goals

    bot_num = packet.num_cars
    elapsed = packet.game_info.seconds_elapsed
    overtime = packet.game_info.is_overtime
    ended = packet.game_info.is_match_ended
    kickoff = packet.game_info.is_kickoff_pause

    for n in range(bot_num):
        team = packet.game_cars[n].team
        name = packet.game_cars[n].name
        goals = packet.teams[team].score
        own_goals = packet.game_cars[n].score_info.own_goals
        bot_list[n][0] = team
        bot_list[n][1] = name
        bot_list[n][2] = goals
        bot_list[n][3] = own_goals

    b_goal = 0
    r_goal = 0
    for n in range(bot_num):
        # Todo: streamline goal detection
        if bot_list[n][0] == 0:
            b_goal = b_goal + bot_list[n][2]
            r_goal = r_goal + bot_list[n][3]
        else:
            r_goal = r_goal + bot_list[n][2]
            b_goal = b_goal + bot_list[n][3]
            total_goals = r_goal + b_goal

    b_team_str = ''
    r_team_str = ''
    for n in range(bot_num):
        # Todo: streamline name
        if bot_list[n][0] == 0:
            if b_team_str != '':
                b_team_str = b_team_str + ' and ' + bot_list[n][1]
            else:
                b_team_str = bot_list[n][1]
        else:
            if r_team_str != '':
                r_team_str = r_team_str + ' and ' + bot_list[n][1]
            else:
                r_team_str = bot_list[n][1]

    if prev_total_goals != total_goals:  # Working
        current_event = 'goal'
    else:
        current_event = 'normal'

    if overtime and not prev_overtime:
        current_state = 'overtime'
    else:
        current_state = 'normal'

    if ended and not prev_ended:
        current_state = 'ended'
    else:
        current_state = 'normal'

    boost_bar(boost)

    set_names('Blue-Name', b_team_str)
    set_names('Orange-Name', r_team_str)

    if current_event == "goal":
        goal_time = time.time() + delay

    if time.time() >= goal_time:
        goal_time = 99999999999999999999999999999999999999
        toggle(True)

    if kickoff:
        toggle(False)

    return

def league_status():
    exists = os.path.isfile(league_file)
    league_on = exists
    if not league_on:
        return None
    return league_data()

def league_data():
    file = open(league_file)
    league_data = json.load(file)
    division = league_data['division']
    show_division(division)
    config = [league_data['blue_config_path'], league_data['orange_config_path']]
    if config[0]:
        set_logo(config[0], config[1])
    return config

def show_division(div_num):
    # TODO: add divisions
    pass

def set_logo(blue_config, orange_config): #reused for logo later
    default_logo = os.path.join(files_path, 'logo.png')

    blue_config_bun = get_bot_config_bundle(blue_config)

    orange_config_bun = get_bot_config_bundle(orange_config)

    blue_logo = blue_config_bun.get_logo_file()
    if blue_logo is None:
        blue_logo = default_logo
    orange_logo = orange_config_bun.get_logo_file()
    if orange_logo is None:
        orange_logo = default_logo

    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == 'RLBot - AutoLeague':
                scene = obs.obs_scene_from_source(scene)
                items = obs.obs_scene_enum_items(scene)
                for item in items:
                    if item is not None:
                        source_t = obs.obs_sceneitem_get_source(item)
                        if obs.obs_source_get_name(source_t) == "Logo-0":
                            source = source_t
                            settings = obs.obs_data_create()
                            obs.obs_data_set_string(settings, "file", blue_logo)
                            obs.obs_source_update(source, settings)
                            obs.obs_data_release(settings)
                        if obs.obs_source_get_name(source_t) == "Logo-1":
                            source = source_t
                            settings = obs.obs_data_create()
                            obs.obs_data_set_string(settings, "file", orange_logo)
                            obs.obs_source_update(source, settings)
                            obs.obs_data_release(settings)
                obs.source_list_release(scenes)
                obs.sceneitem_list_release(items)

def set_names(name, string):
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == 'RLBot - AutoLeague':
                scene = obs.obs_scene_from_source(scene)
                items = obs.obs_scene_enum_items(scene)
                for item in items:
                    if item is not None:
                        source_t = obs.obs_sceneitem_get_source(item)
                        if obs.obs_source_get_name(source_t) == name:
                            source = source_t
                            settings = obs.obs_data_create()
                            obs.obs_data_set_string(settings, "text", str(string))
                            obs.obs_source_update(source, settings)
                            obs.obs_data_release(settings)
                            obs.source_list_release(scenes)
                obs.sceneitem_list_release(items)

def toggle(Visible):
    goal_item = get_scene_item('Goal')
    obs.obs_sceneitem_set_visible(goal_item, Visible)

def hide(props, prop):
    toggle(False)

def show(props, prop):
    toggle(True)

def boost_bar(boost):

    boost_bar_pos = [446, 90]
    boost_bar_size = [210, 20]
    perc_bar = boost[0]

    sceneItem = get_scene_item('Blue-Boost-0')
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, perc_bar[0], 1)
    obs.obs_sceneitem_set_scale(sceneItem, scale2_vec)
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, boost_bar_pos[0] + boost_bar_size[0] * (1-perc_bar[0]), boost_bar_pos[1])
    obs.obs_sceneitem_set_pos(sceneItem, pos_vec)
    # obs.obs_sceneitem_release(sceneItem)

    sceneItem = get_scene_item('Orange-Boost-0')
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, perc_bar[1], 1)
    obs.obs_sceneitem_set_scale(sceneItem, scale2_vec)
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, 1920 - boost_bar_size[0] - boost_bar_pos[0], boost_bar_pos[1])
    obs.obs_sceneitem_set_pos(sceneItem, pos_vec)
    # obs.obs_sceneitem_release(sceneItem)

def do_reset_bar():
    global bot_num
    bot_num = 2
    boost_bar([[0, 0], [0, 0]])
    set_names('Blue-Name', '')
    set_names('Orange-Name', '')

def get_scene_item(name):
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == 'RLBot - AutoLeague':
                scene = obs.obs_scene_from_source(scene)
                items = obs.obs_scene_enum_items(scene)
                for item in items:
                    if item is not None:
                        scene_source = obs.obs_sceneitem_get_source(item)
                        if obs.obs_source_get_name(scene_source) == name:
                            sceneItem = obs.obs_scene_find_sceneitem_by_id(scene, obs.obs_sceneitem_get_id(item))
                            obs.source_list_release(scenes)
                            obs.obs_sceneitem_addref(sceneItem)
                            obs.sceneitem_list_release(items)
                            return sceneItem
                obs.sceneitem_list_release(items)
    obs.source_list_release(scenes)


def set_text_pos():
    pos = [300, 14]
    hardcoded_width = 250
    scale = [1.5, 1.5]

    sceneItem = get_scene_item('Blue-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, pos[0], pos[1])
    obs.obs_sceneitem_set_pos(sceneItem, pos_vec)
    obs.obs_sceneitem_get_scale(sceneItem, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(sceneItem, scale2_vec)
    # obs.obs_sceneitem_release(sceneItem)

    sceneItem = get_scene_item('Orange-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, 1920-pos[0]-hardcoded_width*scale[0], pos[1])
    obs.obs_sceneitem_set_pos(sceneItem, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(sceneItem, scale2_vec)
    # obs.obs_sceneitem_release(sceneItem)

def reset_bar(props, prop):
    do_reset_bar()

def get_settings(name):
    name = name + '.json'
    file = os.path.join(files_path, 'settings', name)
    settings = obs.obs_data_create_from_json_file(file)
    return settings

def auto_setup(props, prop): # Todo: add BO3 and BO5
    global game_item
    global social_item
    global overlay_item
    global bar_0_item
    global blue_cheer_item
    global orange_cheer_item
    global bar_1_item
    global blue_name_item
    global orange_name_item
    global blue_boost_item
    global orange_boost_item
    global boost_0_item
    global boost_1_item
    global goal_item
    global game_source
    global social_source
    global overlay_source
    global bar_0_source
    global blue_cheer_source
    global orange_cheer_source
    global bar_1_source
    global blue_name_source
    global orange_name_source
    global blue_boost_source
    global orange_boost_source
    global boost_0_source
    global boost_1_source
    global goal_source

    if not check_for_scene('RLBot - AutoLeague'):
        main_scene = obs.obs_scene_create('RLBot - AutoLeague')

        # Game Capture
        temp_settings = get_settings('Game Capture')
        game_source = obs.obs_source_create('game_capture', 'Game', temp_settings, None)
        game_item = obs.obs_scene_add(main_scene, game_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(game_source)
        # obs.obs_sceneitem_release(game_item)

        # Social
        temp_settings = get_settings('Social')
        temp_path = os.path.join(files_path, 'social.png')
        obs.obs_data_set_string(temp_settings, 'file', temp_path)
        social_source = obs.obs_source_create('image_source', 'Social', temp_settings, None)
        social_item = obs.obs_scene_add(main_scene, social_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(social_source)
        # obs.obs_sceneitem_release(social_item)

        # Blue-Boost-0
        temp_settings = get_settings('Blue Boost 0')
        blue_boost_0_source = obs.obs_source_create('color_source', 'Blue-Boost-0', temp_settings, None)
        blue_boost_0_item = obs.obs_scene_add(main_scene, blue_boost_0_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(blue_boost_0_source)
        # obs.obs_sceneitem_release(blue_boost_item)

        # Orange-Boost-0
        temp_settings = get_settings('Orange Boost 0')
        orange_boost_0_source = obs.obs_source_create('color_source', 'Orange-Boost-0', temp_settings, None)
        orange_boost_0_item = obs.obs_scene_add(main_scene, orange_boost_0_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(orange_boost_0_source)
        # obs.obs_sceneitem_release(orange_boost_item)

        # RLBot Overlay
        temp_settings = get_settings('RLBot Overlay')
        temp_path = os.path.join(files_path, 'overlay.png')
        obs.obs_data_set_string(temp_settings, 'file', temp_path)
        overlay_source = obs.obs_source_create('image_source', 'Overlay', temp_settings, None)
        overlay_item = obs.obs_scene_add(main_scene, overlay_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(overlay_source)
        # obs.obs_sceneitem_release(overlay_item)

        # Blue-Name
        temp_settings = get_settings('Blue Team Name')
        blue_name_source = obs.obs_source_create('text_gdiplus', 'Blue-Name', temp_settings, None)
        blue_name_item = obs.obs_scene_add(main_scene, blue_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(blue_name_source)
        # obs.obs_sceneitem_release(blue_name_item)

        # Orange-Name
        temp_settings = get_settings('Orange Team Name')
        orange_name_source = obs.obs_source_create('text_gdiplus', 'Orange-Name', temp_settings, None)
        orange_name_item = obs.obs_scene_add(main_scene, orange_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(orange_name_source)
        # obs.obs_sceneitem_release(orange_name_item)

        # Logo-0
        temp_settings = get_settings('Logo')
        temp_path = os.path.join(files_path, 'logo.png')
        obs.obs_data_set_string(temp_settings, 'file', temp_path)
        logo_0_source = obs.obs_source_create('image_source', 'Logo-0', temp_settings, None)
        logo_0_item = obs.obs_scene_add(main_scene, logo_0_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(logo_0_source)
        vec = obs.vec2()
        obs.vec2_set(vec, 663, 10)
        obs.obs_sceneitem_set_pos(logo_0_item, vec)
        obs.vec2_set(vec, 0.25, 0.25)
        obs.obs_sceneitem_set_scale(logo_0_item, vec)
        # obs.obs_sceneitem_release(social_item)

        # Logo-1
        temp_settings = get_settings('Logo')
        temp_path = os.path.join(files_path, 'logo.png')
        obs.obs_data_set_string(temp_settings, 'file', temp_path)
        logo_0_source = obs.obs_source_create('image_source', 'Logo-1', temp_settings, None)
        logo_0_item = obs.obs_scene_add(main_scene, logo_0_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(logo_0_source)
        vec = obs.vec2()
        obs.vec2_set(vec, 1920-100-663, 10)
        obs.obs_sceneitem_set_pos(logo_0_item, vec)
        obs.vec2_set(vec, 0.25, 0.25)
        obs.obs_sceneitem_set_scale(logo_0_item, vec)
        # obs.obs_sceneitem_release(social_item)

        # Goal
        temp_settings = get_settings('Goal')
        temp_path = os.path.join(files_path, 'goal.mov')
        obs.obs_data_set_string(temp_settings, 'local_file', temp_path)
        goal_source = obs.obs_source_create('ffmpeg_source', 'Goal', temp_settings, None)
        goal_item = obs.obs_scene_add(main_scene, goal_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(goal_source)
        # obs.obs_sceneitem_release(goal_item)

        obs.obs_scene_release(main_scene)
        set_text_pos()
        do_reset_bar()
    else:
        print('Scene already exists, please delete or rename RLBot scene before continuing')

# ----------------------------------------------------------

# A function named script_properties defines the properties that the user
# can change for the entire script module itself
def script_properties():

    props = obs.obs_properties_create()

    obs.obs_properties_add_list(props, "files_path", "Overlay files path", obs.OBS_COMBO_TYPE_EDITABLE,
                                    obs.OBS_COMBO_FORMAT_STRING)

    obs.obs_properties_add_list(props, "league_folder", "Auto-League Folder", obs.OBS_COMBO_TYPE_EDITABLE,
                                    obs.OBS_COMBO_FORMAT_STRING)

    obs.obs_properties_add_button(props, "start_button", "Start Script", start_script)
    obs.obs_properties_add_button(props, "stop_button", "Stop Script", stop_script)

    obs.obs_properties_add_float_slider(props, 'delay', 'Goal delay', 0, 5, 0.05)
    obs.obs_properties_add_float_slider(props, 'end_delay', 'End delay', 0, 20, 0.5)

    obs.obs_properties_add_button(props, "reset_button", "Reset Bar", reset_bar)

    obs.obs_properties_add_button(props, "setup_button", "Setup", auto_setup)

    #scriptpath = script_path()

    return props


# A function named script_description returns the description shown to the user
def script_description():
    return '''Shows a overlay everytime a goal is scored. use 1.65 for better timing.
    Use 12 for end delay
    Place the overlay files path and the rlbot.cfg ( used by cleo ) on the settings.'''


# A function named script_update will be called when settings are changed
def script_update(settings):
    global delay
    global end_delay
    global files_path
    global league_folder
    global league_file

    files_path = obs.obs_data_get_string(settings, "files_path")
    league_folder = obs.obs_data_get_string(settings, "league_folder")
    league_file = os.path.join(league_folder, 'current_match.json',)

    delay = obs.obs_data_get_double(settings, "delay")
    end_delay = obs.obs_data_get_double(settings, "end_delay")


def CheckRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    # Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def check_for_scene(name):
    check = False
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == name:
                check = True
    obs.source_list_release(scenes)
    return check

def start():
    global packet_reader
    global bot_num
    global elapsed
    global overtime
    global ended
    global team
    global name
    global total_goals
    global own_goals
    global bot_list
    global goal_time
    global end_time
    global start_time
    global cheer
    global total_blue
    global total_orange
    global boost
    global league_on

    league_on = False

    if CheckRunning('RocketLeague.exe'):
        # Todo: make it wait until it starts, like a timer

        packet_reader = GameTickReader()
        bot_num = 0
        elapsed = 0
        overtime = 0
        ended = 0
        team = 0
        name = ''
        total_goals = 0
        own_goals = 0
        bot_list = [[[], [], [], []], [[], [], [], []]]
        # bot_list = [[bot_n][team][name][goals][owngoals]][[][][][]]]
        goal_time = 99999999999999999999999999999999999999
        end_time = 99999999999999999999999999999999999999
        start_time = 99999999999999999999999999999999999999
        total_blue = 0
        total_orange = 0
        boost = [[0, 0], [0, 0]]
        obs.timer_add(frame_tick, 100)
    else:
        print('Rocket League not running, Aborting!!!')

def start_script(props, prop):
    obs.timer_add(wait_for_game, 500)

def stop_script(props, prop):
    obs.timer_remove(wait_for_game)
    obs.timer_remove(frame_tick)

def wait_for_game():
    if CheckRunning('RocketLeague.exe'):
        obs.timer_remove(wait_for_game)
        start()
    else:
        return

def script_load(settings):
    pass
