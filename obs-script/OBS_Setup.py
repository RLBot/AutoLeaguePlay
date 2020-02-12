import obspython as obs
import os
from PIL import Image

def check_for_scene(name):
    check = False
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == name:
                check = True
    obs.source_list_release(scenes)
    return check

def set_logo(blue_config, orange_config): #reused for logo later
    default_logo = os.path.join(files_path, 'logo.png')

    blue_logo = default_logo
    orange_logo = default_logo

    default_logo_scale = 0.25
    default_logo_size = [400*default_logo_scale, 300*default_logo_scale]

    blue_logo_size = list(Image.open(blue_logo).size)
    blue_scale = default_logo_size[0]/blue_logo_size[0]
    orange_logo_size = list(Image.open(orange_logo).size)
    orange_scale = default_logo_size[0]/orange_logo_size[0]

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

                            vec = obs.vec2()
                            obs.vec2_set(vec, blue_scale, blue_scale)
                            obs.obs_sceneitem_set_scale(item, vec)

                        if obs.obs_source_get_name(source_t) == "Logo-1":
                            source = source_t
                            settings = obs.obs_data_create()
                            obs.obs_data_set_string(settings, "file", orange_logo)
                            obs.obs_source_update(source, settings)
                            obs.obs_data_release(settings)

                            vec = obs.vec2()
                            obs.vec2_set(vec, orange_scale, orange_scale)
                            obs.obs_sceneitem_set_scale(item, vec)

                obs.source_list_release(scenes)
                obs.sceneitem_list_release(items)

def set_dev_name(blue_config, orange_config): #reused for logo later
    default_dev_name = ''

    blue_config_bun = get_bot_config_bundle(blue_config)
    orange_config_bun = get_bot_config_bundle(orange_config)

    blue_dev_name = blue_config_bun.base_agent_config.get('Details', 'developer')
    if blue_dev_name is None:
        blue_dev_name = default_dev_name
    orange_dev_name = orange_config_bun.base_agent_config.get('Details', 'developer')
    if orange_dev_name is None:
        orange_dev_name = default_dev_name

    set_names('Blue-Dev-Name', blue_dev_name)
    set_names('Orange-Dev-Name', orange_dev_name)

def set_names(source_name, string):
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == 'RLBot - AutoLeague':
                scene = obs.obs_scene_from_source(scene)
                items = obs.obs_scene_enum_items(scene)
                for item in items:
                    if item is not None:
                        source_t = obs.obs_sceneitem_get_source(item)
                        if obs.obs_source_get_name(source_t) == source_name:
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
    pos = [290+100, 14]
    hardcoded_width = 250
    hardcoded_height = 26
    scale = [1.5, 1.5]
    #math should make it mirrored but doesnt, gotta add a bit more so looks mirrored
    bit_to_right = 5

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
    obs.vec2_set(pos_vec, 1920-pos[0]-hardcoded_width*scale[0] + bit_to_right, pos[1])
    obs.obs_sceneitem_set_pos(sceneItem, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(sceneItem, scale2_vec)
    # obs.obs_sceneitem_release(sceneItem)

    sceneItem = get_scene_item('Blue-Dev-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, pos[0], pos[1]+hardcoded_height*scale[1])
    obs.obs_sceneitem_set_pos(sceneItem, pos_vec)
    obs.obs_sceneitem_get_scale(sceneItem, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(sceneItem, scale2_vec)
    # obs.obs_sceneitem_release(sceneItem)

    sceneItem = get_scene_item('Orange-Dev-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, 1920-pos[0]-hardcoded_width*scale[0] + bit_to_right, pos[1]+hardcoded_height*scale[1])
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
    global blue_dev_name_item
    global orange_dev_name_item
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

        # Blue-Dev-Name
        temp_settings = get_settings('Blue Dev Name')
        blue_dev_name_source = obs.obs_source_create('text_gdiplus', 'Blue-Dev-Name', temp_settings, None)
        blue_dev_name_item = obs.obs_scene_add(main_scene, blue_dev_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(blue_dev_name_source)
        # obs.obs_sceneitem_release(blue_name_item)

        # Orange-Dev-Name
        temp_settings = get_settings('Orange Dev Name')
        orange_dev_name_source = obs.obs_source_create('text_gdiplus', 'Orange-Dev-Name', temp_settings, None)
        orange_dev_name_item = obs.obs_scene_add(main_scene, orange_dev_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(orange_dev_name_source)
        # obs.obs_sceneitem_release(orange_name_item)

        logo_pos = [300, 10]
        logo_scale = 0.25

        # Logo-0
        temp_settings = get_settings('Logo')
        temp_path = os.path.join(files_path, 'logo.png')
        obs.obs_data_set_string(temp_settings, 'file', temp_path)
        logo_0_source = obs.obs_source_create('image_source', 'Logo-0', temp_settings, None)
        logo_0_item = obs.obs_scene_add(main_scene, logo_0_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(logo_0_source)
        vec = obs.vec2()
        obs.vec2_set(vec, logo_pos[0], logo_pos[1])
        obs.obs_sceneitem_set_pos(logo_0_item, vec)
        obs.vec2_set(vec, logo_scale, logo_scale)
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
        obs.vec2_set(vec, 1920-100-logo_pos[0], logo_pos[1])
        obs.obs_sceneitem_set_pos(logo_0_item, vec)
        obs.vec2_set(vec, logo_scale, logo_scale)
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
    global files_path

    files_path = obs.obs_data_get_string(settings, "files_path")