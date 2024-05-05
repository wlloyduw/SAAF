#
# @author Robert Cordingly
# @author Wes Lloyd
#

import base64
import collections
import inspect
import json
import os
import shutil
import subprocess
import threading
import time
import traceback
import uuid
import re
import time

STOP_THREADS = {}

def cloud_function(platform="aws", config={}, deploy=True, force_deploy=False):
    """_summary_

    Args:
        platform (str, optional): The platform the deploy the function to. Defaults to "aws".
        config (dict, optional): Config dictionary, define any other configuration details here. Defaults to {}.
        deploy (bool, optional): Whether the function should be deplyoed at all. Defaults to True.
        force_deploy (bool, optional): Whether the function should be deployed even if changes are not detected. Defaults to False.
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
            if args[0] != None:
                results = test(function=f, payload=args[0], quiet=True)
            return results
        wrapper.__name__ = f.__name__
        return wrapper
    return decorated

def _deploy_function(name, source, override_platform, override_config, force_deploy):
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
    
    # FaaSET Config
    function_data = _load_faaset_data(name)
    
    platform = override_platform
    if override_platform == "None":
        if function_data["platform"] == "None":
            raise Exception("No platform specified. Please specify a platform.")
        else:
            platform = function_data["platform"]
    
    _check_name_compatibility(name, platform)
    
    # Copy base files for platform.
    _copy_from_platform(name, platform)
    
    # Load the config.
    config = _load_config(name, platform, override_config)
    
    source_hash = base64.b64encode(source.encode('utf-8')).decode('utf-8')
    config_hash = base64.b64encode(str(config).encode('utf-8')).decode('utf-8')

    # Check configs
    if not force_deploy:
        if not _is_changed(function_data, platform, source_hash, config_hash):
            return None

    # Update function file
    function_data["source_hashes"][platform] = source_hash
    function_data["config_hashes"][platform] = config_hash
    function_data["name"] = name
    function_data["platform"] = platform

    # Save function file
    _save_faaset_data(name, function_data)
    _save_function_config(name, platform, config)
    _save_temp_config(name, platform, config)
    _write_handler(name, platform, source)

    deploy(name, platform)
    
    # Check run requirements
    required_parameters = []
    for key in config:
        if config[key] == "FAASET_RUN_REQUIREMENT":
            required_parameters.append(key)
    if len(required_parameters) > 0:
        raise Exception("Missing required parameters to run function: " + str(required_parameters) + "\n Either pass parameters in through the config object parameter or modify default_config.json of the platform or function.")
    

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
    
    platform_config = {}
    if os.path.exists("./platforms/" + platform + "/default_config.json"):
        platform_config = json.load(
            open("./platforms/" + platform + "/default_config.json"))
    else:
        raise Exception("No default_config.json file found for platform: " +
                        platform + ". \n Unknown platform.")

    # Override with function config
    if os.path.exists("./functions/" + name + "/" + platform + "/default_config.json"):
        function_config = json.load(
            open("./functions/" + name + "/" + platform + "/default_config.json"))
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

def _is_changed(function_data, platform, source_hash, config_hash):
    if function_data["platform"] != platform:
        return True
    
    if (platform in function_data["source_hashes"]):
        if (source_hash != function_data["source_hashes"][platform]):
            return True
    
    if (platform in function_data["config_hashes"]):
        if (config_hash != function_data["config_hashes"][platform]):
            return True

    return False

def _load_faaset_data(name):
    faaset_path = "./functions/" + name + "/FAASET.json"
    
    # Create folders...
    if not os.path.isdir("./functions"):
        os.mkdir("./functions")
        if not os.path.isdir("./functions/" + name):
            os.mkdir("./functions/" + name)
    
    function_data = {
        "source_hashes": {},
        "config_hashes": {},
        "platform": "None"
    }
    
    # Load the function data...
    if os.path.exists(faaset_path):
        function_data = json.load(open(faaset_path))
        
    return function_data

def _copy_from_platform(name, platform):
    platform_folder = "./platforms/" + platform
    source_folder = "./functions/" + name + "/" + platform + "/"
    
    if not os.path.exists(platform_folder + "/default_config.json"):
        raise Exception("No default_config.json file found for platform: " +
                        platform + ". \n Unknown platform.")
    
    if not os.path.isdir("./functions/" + name):
        os.mkdir("./functions/" + name)
        
    if not os.path.isdir(source_folder):
        os.mkdir(source_folder)
    
    # loop through all files in folder and copy them to destination if they do not already exist
    for file in os.listdir(platform_folder):
        if os.path.isfile(os.path.join(platform_folder, file)):
            if not (os.path.isfile(os.path.join(source_folder, file))):
                shutil.copy(os.path.join(platform_folder, file), source_folder)
    
    # Load parent platforms
    temp_config = json.load(open(source_folder + "default_config.json"))
    
    # Get files from parent platform...
    if "faaset_parent_platform" in temp_config:
        parent_platform = temp_config["faaset_parent_platform"]
        parent_platform_folder = "./platforms/" + parent_platform
        os.remove(source_folder + "default_config.json")
        for file in os.listdir(parent_platform_folder):
            if os.path.isfile(os.path.join(parent_platform_folder, file)):
                if not (os.path.isfile(os.path.join(source_folder, file))):
                    shutil.copy(os.path.join(parent_platform_folder, file), source_folder)
        parent_config = json.load(open(source_folder + "/default_config.json"))
        for key in temp_config:
            parent_config[key] = temp_config[key]
        json.dump(parent_config, open(source_folder + "/default_config.json", "w"), indent=4)

def _write_handler(name, platform, source_code):
    # Source paths
    source_folder = "./functions/" + name + "/" + platform + "/"
    
    # Write the handler
    handler = open(source_folder + "handler.py", "w")
    handler.write(source_code)
    handler.close()

def _save_faaset_data(name, function_data):
    faaset_path = "./functions/" + name + "/FAASET.json"
    json.dump(function_data, open(faaset_path, "w"), indent=4)

def _save_function_config(name, platform, config):
    source_folder = "./functions/" + name + "/" + platform + "/"
    with open(source_folder + "default_config.json", 'w') as json_file:
        json.dump(config, json_file, indent=4)

def _save_temp_config(name, platform, config):
    source_folder = "./functions/" + name + "/" + platform + "/"
    with open(source_folder + "config.json", 'w') as json_file:
        json.dump(config, json_file, indent=4)

def deploy(name, platform):
    
    if (isinstance(name, collections.Callable)):
        name = name.__name__
    
    source_folder = "./functions/" + name + "/" + platform + "/"
    
    # Run publish.sh
    global STOP_THREADS

    STOP_THREADS[name + platform] = False
    build_watcher = threading.Thread(target=_build_watcher, args=(
        source_folder + "build.log", name, platform,))
    build_watcher.start()
    
    error_watcher = threading.Thread(target=_build_watcher, args=(
        source_folder + "error.log", name, platform,))
    error_watcher.start()

    # Run the build and publih script....
    _run_script(source_folder, "build.sh")
    _run_script(source_folder, "publish.sh")

    STOP_THREADS[name + platform] = True

def _run_script(source_folder, script_name):
    try:
        command = source_folder + script_name + " " + source_folder
        with open(source_folder + "build.log", 'w+') as f, open(source_folder + "error.log", 'w+') as e_f:
            proc = subprocess.Popen(
                command.split(), bufsize=-1, stdout=f, stderr=e_f)
        o, e = proc.communicate()
        time.sleep(0.2) # Make sure the build watcher catches any final output..
    except Exception as e:
        print("An exception occurred running " + script_name + " script: " + str(e))

def reconfigure(function, override_config=None, platform=None):
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

    name = function
    if (isinstance(function, collections.Callable)):
        name = function.__name__
    
    function_data = _load_faaset_data(name)

    if platform is not None:
        function_data['platform'] = platform
        _save_faaset_data(name, function_data)
    else:
        platform = function_data['platform']

    if override_config is not None:
        config = _load_config(name, platform, override_config)
        config_hash = base64.b64encode(str(config).encode('utf-8')).decode('utf-8')

        if (platform in function_data["config_hashes"]):
            if (config_hash != function_data["config_hashes"][platform]):
                function_data["config_hashes"][platform] = config_hash
                _save_faaset_data(name, function_data)
                _save_function_config(name, platform, config)
                _save_temp_config(name, platform, config)
                deploy(name, platform)



def _source_processor(source, functionName):
    prefix = "FAASET_PREFIX"
    source = source.replace("def " + functionName, prefix + "def yourFunction")
    source = source.replace(functionName + "(", "yourFunction(")
    source = prefix + source
    source = re.sub(prefix + '.*?' + prefix, '', source, flags=re.DOTALL)
    source = "# WARNING (Autogenerated Code): Editing this file manually is NOT RECOMMENDED! CHANGES MAY BE LOST!\n" + source
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

def _check_name_compatibility(name, platform):
    if platform == "google" or platform == "google_gen2":
        fixed_name = name.lower().replace("_", "")
        if name != fixed_name:
            raise Exception("Function name must be lowercase and not contain underscores on Google Cloud Functions.")
        

def dynamic_get_payload(main_function, request, references=[], embeds=[]):
    code = inspect.getsource(main_function)
    
    for reference in references:
        code += "\n\n" + inspect.getsource(reference)
                
    index = 0
    for func in embeds:
        embed = inspect.getsource(func)
        embed_encoding = base64.b64encode(embed.encode('utf-8')).decode('utf-8')
        code = code.replace("FAASET_EMBED_" + str(index), embed_encoding)
        index += 1
    
    encoding = base64.b64encode(code.encode('utf-8')).decode('utf-8')
    request['f'] = encoding
    return request

def duplicate(function, source_platform, new_name):
    name = function
    if (isinstance(function, collections.Callable)):
        name = function.__name__
        
    source_folder = "./functions/" + name + "/" + source_platform + "/"
    destination_folder  = "./functions/" + name + "/" + new_name + "/"

    shutil.copytree(source_folder, destination_folder)
    
def clear(function, platform):
    name = function
    if (isinstance(function, collections.Callable)):
        name = function.__name__
        
    source_folder = "./functions/" + name + "/" + platform + "/"
    shutil.rmtree(source_folder)

def test(function, payload, quiet=False, outPath="default", tags={}, platform=None):
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
    
    name = function
    if (isinstance(function, collections.Callable)):
        name = function.__name__

    if platform is None:
        faaset_path = "./functions/" + name + "/FAASET.json"
        function_data = json.load(open(faaset_path))
        platform = function_data["platform"]
    source_folder = "./functions/" + name + "/" + platform + "/"

    try:
        cmd = [source_folder + "run.sh",
               source_folder, str(json.dumps(payload))]
        startTime = time.time()
        proc = subprocess.Popen(
            cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()
        timeSinceStart = round((time.time() - startTime) * 100000) / 100
        out = str(o.decode('ascii'))
        error = str(e.decode('ascii'))
        obj = {}
        try:
            obj = json.loads(out)

            obj["roundTripTime"] = timeSinceStart
            obj["payload"] = payload
            
            if 'runtime' in obj:
                obj['latency'] = round(timeSinceStart - int(obj['runtime']), 2)

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

print("------------------------------------------------------")
print("             Welcome to FaaSET v3.1!")
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