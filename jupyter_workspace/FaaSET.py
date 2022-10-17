#
# @author Robert Cordingly
# @author Wes Lloyd
#

import base64
import inspect
import json
import os
import shutil
import subprocess
import threading
import time
import traceback
import uuid

STOP_THREADS = {}

def cloud_function(platform="aws", config={}, deploy=True, force_deploy=False):
    """_summary_

    Args:
        platform (str, optional): _description_. Defaults to "aws".
        config (dict, optional): _description_. Defaults to {}.
        deploy (bool, optional): _description_. Defaults to True.
        force_deploy (bool, optional): _description_. Defaults to False.
    """

    def decorated(f):
        def wrapper(*args, **kwargs):
            results = None

            functionName = f.__name__
            wrapper.__name__ = functionName

            if deploy:
                source = _source_processor(
                    inspect.getsource(f), functionName)
                _deploy_function(functionName, source,
                                platform, config, force_deploy)
            results = test(function=f, payload=args[0], quiet=True)
            return results
        wrapper.__name__ = f.__name__
        return wrapper
    return decorated


def test(function, payload, quiet=False, outPath="default", tags={}):
    """Runs a function and returns the response object.

    Args:
        function (func): _description_
        payload (obj): _description_
        quiet (bool, optional): _description_. Defaults to False.
        outPath (str, optional): _description_. Defaults to "default".
        tags (dict, optional): _description_. Defaults to {}.

    Returns:
        _type_: _description_
    """
    name = function.__name__
    faaset_path = "./functions/" + name + "/FAASET.json"
    function_data = json.load(open(faaset_path))
    platform = function_data["platform"]
    source_folder = "./functions/" + name + "/" + platform + "/"

    try:
        cmd = [source_folder + "run.sh",
               source_folder, str(json.dumps(payload))]
        proc = subprocess.Popen(
            cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()
        out = str(o.decode('ascii'))
        error = str(e.decode('ascii'))
        obj = {}
        try:
            obj = json.loads(out)

            # Apply tags
            for key in tags:
                obj[key] = tags[key]

            if not quiet:
                print(json.dumps(obj, indent=4))

            # Write output json if outpath is supplied.
            if outPath is not None:
                experiment_path = "./functions/" + name + "/experiments"
                if not os.path.isdir(experiment_path):
                    os.mkdir(experiment_path)
                if not os.path.isdir(experiment_path + "/" + outPath):
                    os.mkdir(experiment_path + "/" + outPath)
                json.dump(obj, open(experiment_path + "/" +
                          outPath + "/" + str(uuid.uuid4()) + ".json", "w"), indent=4)

        except Exception as e:
            print("An exception occurred reading the response:\n--->" + str(e))
            print("---> Command: " + str(cmd))
            print("---> Response: " + out)
            print("---> Error: " + error)
            print("---> Stack Trace:")
            traceback.print_exc()

        return obj
    except Exception as e:
        print("An exception occurred: " + str(e))
        traceback.print_exc()
        return None

def get_config(platform, quiet=False):
    """_summary_

    Args:
        platform (_type_): _description_
        quiet (bool, optional): _description_. Defaults to False.

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """
    
    platform_config = {}
    if os.path.exists("./platforms/" + platform + "/default_config.json"):
        platform_config = json.load(
            open("./platforms/" + platform + "/default_config.json"))
    else:
        raise Exception("No default_config.json file found for platform: " +
                        platform + ". \n Unknown platform.")
    if (not quiet):
        print("Config parameters for " + platform + ":\n" + json.dumps(platform_config, indent=4))
    return platform_config

def _load_config(name, platform, override_config):
    """_summary_

    Args:
        name (_type_): _description_
        platform (_type_): _description_
        override_config (_type_): _description_

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """

    # Load the initial platform config file
    platform_config = get_config(platform, quiet=True)

    # Override with function config
    if os.path.exists("./functions/" + name + "/default_config.json"):
        function_config = json.load(
            open("./functions/" + name + "/default_config.json"))
        for key in function_config.keys():
            platform_config[key] = function_config[key]

    # Override with user supplied config
    for key in override_config.keys():
        platform_config[key] = override_config[key]
    platform_config['function_name'] = name

    # Check for required parameters
    required_parameters = []
    for key in platform_config:
        if platform_config[key] == "FAASET_REQUIREMENT":
            required_parameters.append(key)
    if len(required_parameters) > 0:
        raise Exception("Missing required parameters: " + str(required_parameters) + "\n Either pass parameters in through the config object parameter or modify default_config.json of the platform or function.")

    return platform_config

def _deploy_function(name, source, platform, override_config, force_deploy):
    """_summary_

    Args:
        name (_type_): _description_
        source (_type_): _description_
        platform (_type_): _description_
        override_config (_type_): _description_
        force_deploy (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    # Paths
    faaset_path = "./functions/" + name + "/FAASET.json"
    platform_folder = "./platforms/" + platform
    source_folder = "./functions/" + name + "/" + platform + "/"

    # Create folders...
    if not os.path.isdir("./functions"):
        os.mkdir("./functions")
    if not os.path.isdir("./functions/" + name):
        os.mkdir("./functions/" + name)
    if not os.path.isdir("./functions/" + name + "/" + platform):
        os.mkdir("./functions/" + name + "/" + platform)

    config = _load_config(name, platform, override_config)

    function_data = {
        "source_hash": {platform: ""},
        "platform": platform
    }

    if os.path.exists(faaset_path):
        function_data = json.load(open(faaset_path))

    source_hash = base64.b64encode(source.encode('utf-8')).decode('utf-8')

    if not force_deploy:
        if platform in function_data["source_hash"]:
            if source_hash == function_data["source_hash"][platform]:
                if platform != function_data["platform"]:
                    # Platform swap no source change...
                    function_data["platform"] = platform
                    json.dump(function_data, open(faaset_path, "w"), indent=4)
                return None

    # Update function file
    function_data["source_hash"][platform] = source_hash
    function_data["name"] = name
    function_data["platform"] = platform

    # Save function file
    json.dump(function_data, open(faaset_path, "w"), indent=4)

    # Write the handler
    handler = open(source_folder + "handler.py", "w")
    handler.write(source)
    handler.close()

    with open(source_folder + "config.json", 'w') as json_file:
        json.dump(config, json_file, indent=4)

    # loop through all files in folder and copy them to destination if they do not already exist
    for file in os.listdir(platform_folder):
        if os.path.isfile(os.path.join(platform_folder, file)):
            if not (os.path.isfile(os.path.join(source_folder, file))):
                shutil.copy(os.path.join(platform_folder, file), source_folder)

    # Run publish.sh
    global STOP_THREADS

    STOP_THREADS[name + platform] = False
    build_watcher = threading.Thread(target=_build_watcher, args=(
        source_folder + "build.log", name, platform,))
    build_watcher.start()

    # Run the build and publih script....
    _run_script(source_folder, "build.sh")
    _run_script(source_folder, "publish.sh")

    STOP_THREADS[name + platform] = True

def _run_script(source_folder, script_name):
    try:
        command = source_folder + script_name + " " + source_folder
        with open(source_folder + "build.log", 'w+') as f:
            proc = subprocess.Popen(
                command.split(), bufsize=-1, stdout=f, stderr=subprocess.PIPE)
        o, e = proc.communicate()
        time.sleep(0.2) # Make sure the build watcher catches any final output..
    except Exception as e:
        print("An exception occurred running " + script_name + " script: " + str(e))

def reconfigure(function, config={}, platform=None):
    """_summary_

    Args:
        function (_type_): _description_
        config (dict, optional): _description_. Defaults to {}.
        platform (_type_, optional): _description_. Defaults to None.

    Raises:
        Exception: _description_

    Returns:
        _type_: None
    """

    name = function.__name__
    faaset_path = "./functions/" + name + "/FAASET.json"
    
    function_data = {}
    if os.path.exists(faaset_path):
        function_data = json.load(open(faaset_path))
    else:
        raise Exception("Unknown function: " + name)

    if platform is None:
        platform = function_data["platform"]
    else:
        function_data["platform"] = platform
        json.dump(function_data, open(faaset_path, "w"), indent=4)
        print("Platform changed to: " + platform)
        
    if config == {}:
        return None
        
    source_folder = "./functions/" + name + "/" + platform + "/"

    # Load
    config = _load_config(name, platform, config)

    with open(source_folder + "config.json", 'w') as json_file:
        json.dump(config, json_file, indent=4)

    # Run publish.sh
    global STOP_THREADS

    STOP_THREADS[name + platform] = False
    build_watcher = threading.Thread(target=_build_watcher, args=(
        source_folder + "build.log", name, platform,))
    build_watcher.start()

    _run_script(source_folder, "publish.sh")

    STOP_THREADS[name + platform] = True


def _source_processor(source, functionName):
    source = source.replace("def " + functionName,
                            "\"\"\"\n\ndef yourFunction")
    source = source.replace(functionName + "(", "yourFunction(")
    source = "\"\"\" AUTOMATICALLY COMMENTED OUT BY FaaSET \n" + source
    return source


def _build_watcher(file_name, name, platform):
    """_summary_

    Args:
        file_name (_type_): _description_
        name (_type_): _description_
        platform (_type_): _description_

    Returns:
        _type_: _description_
    """

    console_contents = ""
    while (True):
        global STOP_THREADS
        try:
            progress = open(file_name, "r")
            data = progress.read()
            progress.close()
            print_data = data.replace(console_contents, "")
            if (print_data != ""):
                print(print_data, end="")
            console_contents = data
        except:
            pass
        if (STOP_THREADS[name + platform]):
            break
        time.sleep(0.1)
    return None


print("------------------------------------------------------")
print("             Welcome to FaaSET v3.0!")
print("------------------------------------------------------")

platforms_directory = os.scandir("./platforms")
print("Available platforms: ", end=" ")
for platform in platforms_directory:
    try:
        if platform.is_dir():
            print(platform.name, end=". ")
    except:
        pass
print("")
print("------------------------------------------------------")

if not os.path.exists("./functions"):
    os.mkdir("./functions")

f_directory = os.scandir("./functions")
print("Loaded functions: ", end=" ")
for func in f_directory:
    try:
        if func.is_dir():
            if (os.path.exists("./functions/" + func.name + "/FAASET.json")):
                f = json.load(
                    open("./functions/" + func.name + "/FAASET.json", "r"))
                source = "@cloud_function(platform='" + f['platform'] + \
                    "', deploy=False)\ndef " + func.name + \
                    "(request, context):\n    pass"
                exec(source)
                print(func.name, end=". ")
            elif (os.path.exists("./functions/" + func.name + "/.faaset.json")):
                print(func.name + " (Incompatible)", end=". ")
            else:
                print(func.name + " (Unknown)", end=". ")
    except Exception as e:
        print(str(e))
        pass
print("")

if __name__ == "__main__":
    pass