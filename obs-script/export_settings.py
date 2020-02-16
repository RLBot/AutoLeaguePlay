import obspython as obs
import os

def export(props, prop):
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for scene in scenes:
            scene_name = obs.obs_source_get_name(scene)
            scene = obs.obs_scene_from_source(scene)
            items = obs.obs_scene_enum_items(scene)
            for item in items:
                if item is not None:
                    scene_source = obs.obs_sceneitem_get_source(item)

                    sceneItem = obs.obs_scene_find_sceneitem_by_id(scene, obs.obs_sceneitem_get_id(item))

                    sceneSettings = obs.obs_sceneitem_get_private_settings(sceneItem)
                    file = os.path.join(export_path, scene_name, ite)
                    obs.obs_data_save_json(sceneSettings, file)
                    obs.source_list_release(scenes)
                    obs.obs_sceneitem_addref(sceneItem)
                    obs.sceneitem_list_release(items)
            obs.sceneitem_list_release(items)
       obs.source_list_release(scenes)

# ----------------------------------------------------------

# A function named script_properties defines the properties that the user
# can change for the entire script module itself
def script_properties():

    props = obs.obs_properties_create()

    obs.obs_properties_add_list(props, "export_path", "Json export path", obs.OBS_COMBO_TYPE_EDITABLE,
                                    obs.OBS_COMBO_FORMAT_STRING)

    obs.obs_properties_add_button(props, "export_button", "Export", export)

    return props


# A function named script_description returns the description shown to the user
def script_description():
    return '''Shows a overlay everytime a goal is scored. use 1.65 for better timing.
    Place the overlay files path and the rlbot.cfg ( used by cleo ) on the settings.'''


# A function named script_update will be called when settings are changed
def script_update(settings):
    global export_path
    export_path = obs.obs_data_get_string(settings, "export_path")