import ipywidgets as widgets
from ipywidgets import interact, interact_manual, fixed
import subprocess
import os
import json
import FaaSET
import collections

def _open_path(button):
    path = button.tooltip
    command = "code " + path
    proc = subprocess.Popen(
        command.split(), bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = proc.communicate()
    
def _reconfigure(button):
    print("Reconfiguring...")
    args = button.tooltip.split("/")
    function = args[0]
    platform = args[1]
    FaaSET.reconfigure(function=function, platform=platform)
    
def _redeploy(button):
    print("Redeploying...")
    args = button.tooltip.split("/")
    function = args[0]
    platform = args[1]
    config_path = "./functions/" + function + "/" + platform + "/" + "default_config.json"
    
    # load config json
    config = json.load(open(config_path))
    version = str(round(float(config["version"]) + 0.1, 1))
    
    FaaSET.reconfigure(function=function, platform=platform, override_config={"version": version})
    
def ui(function):
    name = function
    if (isinstance(function, collections.Callable)):
        name = function.__name__
    function_path = "./functions/" + name + "/"
    sub_folders = [ f.path for f in os.scandir(function_path) if f.is_dir() ]
    faaset_path = function_path + "FAASET.json"
    function_data = {}
    if os.path.exists(faaset_path):
        function_data = json.load(open(faaset_path))
    else:
        raise Exception("Unknown function: " + name)
    
    out = widgets.Output()
    platform = function_data["platform"]
    source_folder = function_path + platform + "/"
    
    config_button = widgets.Button(
        description='Config',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip=source_folder + "default_config.json",
        icon='list' # (FontAwesome names without the `fa-` prefix)
    )
    config_button.on_click(_open_path)
    
    buttons = widgets.HBox([config_button])
    
    source_button = widgets.Button(
        description='Source',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip=source_folder,
        icon='folder-open' # (FontAwesome names without the `fa-` prefix)
    )
    source_button.on_click(_open_path)
    
    reconfigure_button = widgets.Button(
        description='Reconfigure',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip=name + "/" + platform,
        icon='gear' # (FontAwesome names without the `fa-` prefix)
    )
    reconfigure_button.on_click(_reconfigure)
    
    redeploy_button = widgets.Button(
        description='Redeploy',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip=name + "/" + platform,
        icon='rocket' # (FontAwesome names without the `fa-` prefix)
    )
    redeploy_button.on_click(_redeploy)
    
    platforms = []
    for folder in sub_folders:
        plat = folder.replace(function_path, "")
        if plat != "experiments":
            platforms.append(plat)
    
    if len(platforms) == 0:
        raise Exception("No function deployments to any platform for function: " + name)
    
    platform_dropdown = widgets.Dropdown(options = platforms, value = platform)
    
    def on_change(change):
        if change['type'] == 'change' and change['name'] == 'value':
            source_button.tooltip = "./functions/" + name + "/" + change['new'] + "/" 
            config_button.tooltip = "./functions/" + name + "/" + change['new'] + "/" + "default_config.json"
            reconfigure_button.tooltip = name + "/" + change['new']
            redeploy_button.tooltip = name + "/" + change['new']
    platform_dropdown.observe(on_change)
    
    buttons = widgets.HBox([platform_dropdown, source_button, config_button, reconfigure_button, redeploy_button])
    
    return buttons

if __name__ == "__main__":
    pass