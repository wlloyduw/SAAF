import ipywidgets as widgets
from ipywidgets import interact, interact_manual, fixed
import subprocess
import os
import json
import FaaSET
import collections
from IPython.display import clear_output
from IPython.display import display

    
class UI:
    def __init__(self, function):
        self.function = function
        if (isinstance(self.function, collections.Callable)):
            name = self.function.__name__
        self.name = function.__name__
        self.function_path = "./functions/" + name + "/"
        display(self.render())
        
    def render(self):
        sub_folders = [ f.path for f in os.scandir(self.function_path) if f.is_dir() ]
        faaset_path = self.function_path + "FAASET.json"
        function_data = {}
        if os.path.exists(faaset_path):
            function_data = json.load(open(faaset_path))
        else:
            raise Exception("Unknown function: " + self.name)

        out = widgets.Output()
        self.platform = function_data["platform"]
        self.source_folder = self.function_path + self.platform + "/"

        config_button = widgets.Button(
            description='Config',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            #tooltip=source_folder + "default_config.json",
            icon='list' # (FontAwesome names without the `fa-` prefix)
        )
        config_button.on_click(self._open_config)

        buttons = widgets.HBox([config_button])

        source_button = widgets.Button(
            description='Source',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            #tooltip=source_folder,
            icon='folder-open' # (FontAwesome names without the `fa-` prefix)
        )
        source_button.on_click(self._open_source)

        reconfigure_button = widgets.Button(
            description='Reconfigure',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            #tooltip=name + "/" + platform,
            icon='gear' # (FontAwesome names without the `fa-` prefix)
        )
        reconfigure_button.on_click(self._reconfigure)

        redeploy_button = widgets.Button(
            description='Redeploy',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            #tooltip=name + "/" + platform,
            icon='rocket' # (FontAwesome names without the `fa-` prefix)
        )
        redeploy_button.on_click(self._redeploy)

        platforms = []
        for folder in sub_folders:
            plat = folder.replace(self.function_path, "")
            if plat != "experiments":
                platforms.append(plat)

        if len(platforms) == 0:
            raise Exception("No function deployments to any platform for function: " + self.name)

        platform_dropdown = widgets.Dropdown(options = platforms, value = self.platform)

        def on_change(change):
            if change['type'] == 'change' and change['name'] == 'value':
                source_button.tooltip = "./functions/" + self.name + "/" + change['new'] + "/" 
                config_button.tooltip = "./functions/" + self.name + "/" + change['new'] + "/" + "default_config.json"
                reconfigure_button.tooltip = self.name + "/" + change['new']
                redeploy_button.tooltip = self.name + "/" + change['new']
        platform_dropdown.observe(on_change)

        buttons = widgets.HBox([platform_dropdown, source_button, config_button, reconfigure_button, redeploy_button])

        return buttons
    
    def _open_config(self, button):
        clear_output(wait=True)
        display(self.render())
        path = self.source_folder + "default_config.json"
        print("Open: " + path)
        command = "code " + path
        proc = subprocess.Popen(
            command.split(), bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()
    
    def _open_source(self, button):
        clear_output(wait=True)
        display(self.render())
        path = self.source_folder
        print("Open: " + path)
        command = "code " + path
        proc = subprocess.Popen(
            command.split(), bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()
        
    def _reconfigure(self, button):
        print("Reconfiguring...")
        function = self.name
        platform = self.platform
        FaaSET.reconfigure(function=function, platform=platform)
        clear_output(wait=True)
        display(self.render())
        
    def _redeploy(self, button):
        print("Redeploying...")
        function = self.name
        platform = self.platform
        config_path = "./functions/" + function + "/" + platform + "/" + "default_config.json"
        
        # load config json
        config = json.load(open(config_path))
        version = str(round(float(config["version"]) + 0.1, 1))
        
        FaaSET.reconfigure(function=function, platform=platform, override_config={"version": version})
        clear_output(wait=True)
        display(self.render())

if __name__ == "__main__":
    pass