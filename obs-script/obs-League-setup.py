import obspython as obs
import os
# Todo: add cheer bar back


def script_unload():
    pass


def set_default_division():
    # TODO: add divisions
    pass


def set_default_logo():
    default_logo = os.path.join(files_path, 'logo.png')
    default_logo_scale = 0.25

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
                            obs.obs_data_set_string(settings, "file", default_logo)
                            obs.obs_source_update(source, settings)
                            obs.obs_data_release(settings)

                            vec = obs.vec2()
                            obs.vec2_set(vec, default_logo_scale, default_logo_scale)
                            obs.obs_sceneitem_set_scale(item, vec)

                        if obs.obs_source_get_name(source_t) == "Logo-1":
                            source = source_t
                            settings = obs.obs_data_create()
                            obs.obs_data_set_string(settings, "file", default_logo)
                            obs.obs_source_update(source, settings)
                            obs.obs_data_release(settings)

                            vec = obs.vec2()
                            obs.vec2_set(vec, default_logo_scale, default_logo_scale)
                            obs.obs_sceneitem_set_scale(item, vec)

                obs.source_list_release(scenes)
                obs.sceneitem_list_release(items)


def set_default_dev_name():
    default_dev_name = ''

    set_names('Blue-Dev-Name', default_dev_name)
    set_names('Orange-Dev-Name', default_dev_name)


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


def set_default_goal_visibility():
    goal_scene_item = get_scene_item('Goal')
    obs.obs_sceneitem_set_visible(goal_scene_item, False)


def set_default_boost():
    boost_bar_pos = [446, 90]
    boost_bar_size = [210, 20]
    perc_bar = [0, 0]

    scene_item = get_scene_item('Blue-Boost-0')
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, perc_bar[0], 1)
    obs.obs_sceneitem_set_scale(scene_item, scale2_vec)
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, boost_bar_pos[0] + boost_bar_size[0] * (1-perc_bar[0]), boost_bar_pos[1])
    obs.obs_sceneitem_set_pos(scene_item, pos_vec)

    scene_item = get_scene_item('Orange-Boost-0')
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, perc_bar[1], 1)
    obs.obs_sceneitem_set_scale(scene_item, scale2_vec)
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, 1920 - boost_bar_size[0] - boost_bar_pos[0], boost_bar_pos[1])
    obs.obs_sceneitem_set_pos(scene_item, pos_vec)


def reset_defaults(props=0, prop=0):  # TODO: Reset everything, not only partial stuff
    set_default_boost()
    set_default_goal_visibility()
    set_default_dev_name()
    set_default_logo()
    set_default_division()


def get_scene_item(scene_item_name):  # TODO: investigate the fact that the function never releases 'scenes' nor 'items'
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == 'RLBot - AutoLeague':
                scene = obs.obs_scene_from_source(scene)
                items = obs.obs_scene_enum_items(scene)
                for item in items:
                    if item is not None:
                        scene_source = obs.obs_sceneitem_get_source(item)
                        if obs.obs_source_get_name(scene_source) == scene_item_name:
                            scene_item = obs.obs_scene_find_sceneitem_by_id(scene, obs.obs_sceneitem_get_id(item))
                            obs.source_list_release(scenes)
                            obs.obs_sceneitem_addref(scene_item)
                            obs.sceneitem_list_release(items)
                            return scene_item
                obs.sceneitem_list_release(items)
    obs.source_list_release(scenes)


def check_for_scene(scene_name):
    check = False
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            if obs.obs_source_get_name(scene) == scene_name:
                check = True
    obs.source_list_release(scenes)
    return check


def set_text_pos():  # TODO: dont hardcode resolutions
    pos = [290+100, 14]
    hardcoded_width = 250
    hardcoded_height = 26
    scale = [1.5, 1.5]
    # math should make it mirrored but doesnt, gotta add a bit more so looks mirrored
    bit_to_right = 5

    scene_item = get_scene_item('Blue-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, pos[0], pos[1])
    obs.obs_sceneitem_set_pos(scene_item, pos_vec)
    obs.obs_sceneitem_get_scale(scene_item, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(scene_item, scale2_vec)

    scene_item = get_scene_item('Orange-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, 1920-pos[0]-hardcoded_width*scale[0] + bit_to_right, pos[1])
    obs.obs_sceneitem_set_pos(scene_item, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(scene_item, scale2_vec)

    scene_item = get_scene_item('Blue-Dev-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, pos[0], pos[1]+hardcoded_height*scale[1])
    obs.obs_sceneitem_set_pos(scene_item, pos_vec)
    obs.obs_sceneitem_get_scale(scene_item, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(scene_item, scale2_vec)

    scene_item = get_scene_item('Orange-Dev-Name')
    pos_vec = obs.vec2()
    obs.vec2_set(pos_vec, 1920-pos[0]-hardcoded_width*scale[0] + bit_to_right, pos[1]+hardcoded_height*scale[1])
    obs.obs_sceneitem_set_pos(scene_item, pos_vec)
    scale2_vec = obs.vec2()
    obs.vec2_set(scale2_vec, scale[0], scale[1])
    obs.obs_sceneitem_set_scale(scene_item, scale2_vec)


def get_settings(setting_name):
    setting_name = setting_name + '.json'
    file = os.path.join(files_path, 'settings', setting_name)
    settings = obs.obs_data_create_from_json_file(file)
    return settings


def auto_setup(props=0, prop=0):  # Todo: add BO3 and BO5
    if not check_for_scene('RLBot - AutoLeague'):
        main_scene = obs.obs_scene_create('RLBot - AutoLeague')

        # Game Capture
        temp_settings = get_settings('Game Capture')
        game_source = obs.obs_source_create('game_capture', 'Game', temp_settings, None)
        obs.obs_scene_add(main_scene, game_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(game_source)

        # Social
        temp_settings = get_settings('Social')
        temp_path = os.path.join(files_path, 'social.png')
        obs.obs_data_set_string(temp_settings, 'file', temp_path)
        social_source = obs.obs_source_create('image_source', 'Social', temp_settings, None)
        obs.obs_scene_add(main_scene, social_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(social_source)

        # RLBot Overlay
        temp_settings = get_settings('RLBot Overlay')
        temp_path = os.path.join(files_path, 'overlay.png')
        obs.obs_data_set_string(temp_settings, 'file', temp_path)
        overlay_source = obs.obs_source_create('image_source', 'Overlay', temp_settings, None)
        obs.obs_scene_add(main_scene, overlay_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(overlay_source)

        # Blue-Name
        temp_settings = get_settings('Blue Team Name')
        blue_name_source = obs.obs_source_create('text_gdiplus', 'Blue-Name', temp_settings, None)
        obs.obs_scene_add(main_scene, blue_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(blue_name_source)

        # Orange-Name
        temp_settings = get_settings('Orange Team Name')
        orange_name_source = obs.obs_source_create('text_gdiplus', 'Orange-Name', temp_settings, None)
        obs.obs_scene_add(main_scene, orange_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(orange_name_source)

        # Blue-Dev-Name
        temp_settings = get_settings('Blue Dev Name')
        blue_dev_name_source = obs.obs_source_create('text_gdiplus', 'Blue-Dev-Name', temp_settings, None)
        obs.obs_scene_add(main_scene, blue_dev_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(blue_dev_name_source)

        # Orange-Dev-Name
        temp_settings = get_settings('Orange Dev Name')
        orange_dev_name_source = obs.obs_source_create('text_gdiplus', 'Orange-Dev-Name', temp_settings, None)
        obs.obs_scene_add(main_scene, orange_dev_name_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(orange_dev_name_source)

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

        # Goal
        temp_settings = get_settings('Goal')
        temp_path = os.path.join(files_path, 'goal.mov')
        obs.obs_data_set_string(temp_settings, 'local_file', temp_path)
        goal_source = obs.obs_source_create('ffmpeg_source', 'Goal', temp_settings, None)
        obs.obs_scene_add(main_scene, goal_source)
        obs.obs_data_release(temp_settings)
        obs.obs_source_release(goal_source)

        obs.obs_scene_release(main_scene)
        reset_defaults()

    else:

        print('Scene already exists, please delete or rename RLBot scene before continuing')


# ----------------------------------------------------------

# A function named script_properties defines the properties that the user
# can change for the entire script module itself
def script_properties():

    props = obs.obs_properties_create()
    obs.obs_properties_add_list(props, "files_path", "Overlay files path", obs.OBS_COMBO_TYPE_EDITABLE,
                                obs.OBS_COMBO_FORMAT_STRING)
    obs.obs_properties_add_button(props, "reset_button", "Reset to default", reset_defaults)
    obs.obs_properties_add_button(props, "setup_button", "Setup", auto_setup)
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


def script_load(settings):
    pass
