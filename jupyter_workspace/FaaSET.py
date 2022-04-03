#
# @author Robert Cordingly
# @author Wes Lloyd
#
from math import fabs
import pandas as pd
import numpy as np
import json
import os
from enum import Enum
import subprocess
import pathlib
from glob import glob
import shutil
import inspect
import threading
import time
import uuid
from tqdm.notebook import tqdm, trange
import traceback
import base64

from IPython.display import clear_output, display, HTML, IFrame, FileLink
from IPython.display import JSON

print("------------------------------------------------------")
print("Welcome to FaaSET v2.0! Some things have changed when")
print("compared to v1.0. RunModes and the Containerize arguments")
print("have been removed in favor of more available Platforms.")
print("Platforms is no longer a list and now functions can")
print("only be deployed to a single platform at a time.")
print("If you are using a older notebook that has not been")
print("updated things will be broken. Please fix them. ")
print("------------------------------------------------------")

# Load json file platforms.json
platformData = {}
platforms_directory = os.scandir("./platforms")
print("Loaded platforms: ", end=" ")
for platform in platforms_directory:
    try:
        if platform.is_dir():
            platform = json.load(open("./platforms/" + platform.name + "/.default_config.json", "r"))
            platformID = platform['id']
            platformData[platformID] = platform
            print(platformID, end=". ")
    except:
        pass
print("")
print("------------------------------------------------------")

startPath = pathlib.Path().absolute()

def cloud_function(platform="AWS", 
                   config={}, 
                   references=[],
                   deploy=True):
    
    def decorated(f):
        def wrapper(*args, **kwargs):
            results = None
                
            functionName = f.__name__
            wrapper.__name__ = functionName
            
            if deploy:
                source = source_processor(inspect.getsource(f), functionName, references)
                deploy_function(functionName, source, platform, config)
            results = test(function=f, payload=args[0], quiet=True)
            return results
        wrapper.__name__ = f.__name__
        return wrapper
    return decorated
    
    
# Load existing functions...
f_data = {}
f_directory = os.scandir("./functions")
print("Loaded functions: ", end=" ")
for func in f_directory:
    try:
        if func.is_dir():
            f = json.load(open("./functions/" + func.name + "/.faaset.json", "r"))
            source = "@cloud_function(platform='" + f['platform'] + "', deploy=False)\ndef " + func.name + "(request, context):\n    pass"
            exec(source)
            print(func.name, end=". ")
    except Exception as e:
        print(str(e))
        pass
print("")

stop_threads = {}
globalConfig = None
    
def test(function, payload, quiet=False, updateStats=True, outPath="default", tags={}):
    name = function.__name__
    
    try:
        cmd = ["./functions/" + name + "/run.sh", "./functions/" + name + "/", str(json.dumps(payload))]
        proc = subprocess.Popen( cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                
            if updateStats:
                functionData = json.load(open("./functions/" + name + "/.faaset.json"))
                if 'stats' in functionData:
                    functionData['stats']['invocations'] += 1
                    if 'runtime' in obj:
                        functionData['stats']['total_runtime'] += obj['runtime']
                else:
                    functionData['stats'] = {}
                    functionData['stats']['invocations'] = 1
                    if 'runtime' in obj:
                        functionData['stats']['total_runtime'] = obj['runtime']
                    else:
                        functionData['stats']['total_runtime'] = 0
                json.dump(functionData, open("./functions/" + name + "/.faaset.json", "w"), indent=4)
            
            # Write output json if outpath is supplied.
            if outPath is not None:
                if not os.path.isdir("./functions/" + name + "/experiments"):
                    os.mkdir("./functions/" + name + "/experiments") 
                if not os.path.isdir("./functions/" + name + "/experiments/" + outPath):
                    os.mkdir("./functions/" + name + "/experiments/" + outPath)
                json.dump(obj, open("./functions/" + name + "/experiments/" + outPath + "/" + str(uuid.uuid4()) + ".json", "w"), indent=4)
            
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

def run_experiment(function, experiment, platform="AWS", config={}):
    """Execute complex experiments using this function. This function leverages the FaaS Runner application
        to automate experiments and import the results as a pandas dataframe.

    Args:
        function (method): The cloud function to test.
        experiment ([type]): A json object containing FaaS Runner experiment parameters. See the FaaS Runner reference
                for detail on each experiment parameter: https://github.com/wlloyduw/SAAF/tree/master/test
        config (obj):  Context object to supply other required parameters to the function such as Lambda ARNs.
        platform (int): The platform you would like to run the experiment on to. Define platform with the Platform enum.

    Returns:
        dataframe: A pandas dataframe containing all the information from each request. 
    """
    
    functionName = function.__name__
    
    if config == None:
        config = platformData[platform]
    
    global startPath
    os.chdir(startPath)
    data = None
    
    global stop_threads
    stop_threads["experiment"] = False
    
    exp_id = functionName + "-" + str(uuid.uuid4())
    if 'name' in experiment:
        exp_id = functionName + "-" + experiment['name'] + "-" + str(uuid.uuid4())

    print("Running experiment: " + exp_id)
    
    # Create function file...
    function = {}
    function['platform'] = platformData['faas_runner_platform']
    function['function'] = functionName
    function['source'] = "../jupyter_workspace/src/functions/" + functionName + "/config.json"
    function['endpoint'] = ""
    with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
        json.dump(function, json_file, indent=4)
    
    # Set default values
    experiment["outputGroups"] = []
    experiment["ignoreFromGroups"] = []
    experiment["ignoreByGroup"] = {}
    experiment["combineSheets"] = True
    
    with open('../../test/experiments/interactiveExperiment.json', 'w') as json_file:
        json.dump(experiment, json_file, indent=4)
        
    currentPath = pathlib.Path().absolute()
    os.chdir("../../test")
    # try:
    #     shutil.rmtree("history/interactiveExperiment")
    # except:
    #     pass
    
    progressWatcher = threading.Thread(target=progress_watcher, 
        args=(experiment['runs'], experiment['iterations'], len(experiment['memorySettings']), "experiment",))
    progressWatcher.start()
    
    try:
        
        historyPath = "history/interactiveExperiment/" + exp_id +"/"
        command = "./faas_runner.py -f functions/interactiveFunction.json -e experiments/interactiveExperiment.json -o " + historyPath
        data = subprocess.check_output(command.split()).decode('ascii')
        #csvReport = glob("history/interactiveExperiment/" + exp_id +"/*.csv")[0]
        #command = "./tools/report_splitter.py " + csvReport
        #subprocess.check_output(command.split()).decode('ascii')
        
        # Copy all json files into combined folder
        try:
            os.mkdir(os.path.join(historyPath, "combined"))
        except:
            pass
        for folder in os.listdir(historyPath):
            if os.path.isdir(os.path.join(historyPath, folder)):
                for file in os.listdir(os.path.join(historyPath, folder)):
                    os.system("mv {} {}".format(os.path.join(historyPath, folder, file), os.path.join(historyPath, "combined", file)))
                try:
                    if (folder != "combined"):
                        os.rmdir(os.path.join(historyPath, folder))
                except:
                    pass
        
        # Compile results from combined folder
        command = "./compile_results.py " +  historyPath + "combined" + " " + "experiments/interactiveExperiment.json"
        subprocess.check_output(command.split()).decode('ascii')
        
        command = "./tools/report_splitter.py " + historyPath + "combined/compiled-results-interactiveExperiment.csv"
        subprocess.check_output(command.split()).decode('ascii')
        
        # Generate resport
        reportPath = historyPath + "combined/compiled-results-interactiveExperiment - split"
        data = pd.read_csv(reportPath + "/Raw results of each run.csv")
    except Exception as e:
        print(e)
    
    stop_threads["experiment"] = True
    progressWatcher.join()
    
    os.chdir(currentPath)
    return data





#########################################################################
#                                                                       #
#           ALL FURTHER METHODS ARE CALLED BY OTHER METHODS             #
#                   NOT TO BE EXECUTED DIRECTLY                         #
#                                                                       #
#########################################################################

def deploy_function(name, source, platform, config):
    # Create functions folder...
    if not os.path.isdir("./functions"):
        os.mkdir("./functions")
    if not os.path.isdir("./functions/" + name):
        os.mkdir("./functions/" + name)
    
    functionData = {
        "source_hash": ""
    }
    
    if os.path.exists("./functions/" + name + "/.faaset.json"):
        functionData = json.load(open("./functions/" + name + "/.faaset.json"))
        
        if platform != functionData['platform']:
            print("Platform changed! Please move or delete ./function/" + name + " folder to continue. Previous platform: Platform." + functionData['platform'])
            return None
    
    # Load default config if exists in function folder.
    # Otherwise use the platform one.
    defaultConfig = platformData[platform]    
    if os.path.exists("./functions/" + name + "/.default_config.json"):
        defaultConfig = json.load(open("./functions/" + name + "/.default_config.json"))
    
    # Override default values if config is provided.
    for key in defaultConfig.keys():
        if key not in config:
            config[key] = defaultConfig[key]
    config['function_name'] = name

    sourceHash = base64.b64encode(source.encode('utf-8')).decode('utf-8')
    
    if sourceHash == functionData["source_hash"]:
        return None

    # Update function file...
    functionData["source_hash"] = sourceHash
    functionData["name"] = name
    functionData["platform"] = platform
    functionData["config"] = config
    
    # save json file
    json.dump(functionData, open("./functions/" + name + "/.faaset.json", "w"), indent=4)

    # Write the handler
    textfile = open("./functions/" + name + "/handler.py", "w")
    textfile.write(source)
    textfile.close()
    
    with open("./functions/" + name + "/config.json", 'w') as json_file:
        json.dump(config, json_file, indent=4)
    
    folder = config['location']
    destination = "./functions/" + name + "/"
    
    # loop through all files in folder and copy them to destination if they do not already exist
    for file in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, file)):
            if not (os.path.isfile(os.path.join(destination, file))):
                shutil.copy(os.path.join(folder, file), destination)
    
    # Run publish.sh
    global stop_threads
    
    stop_threads[name] = False
    buildWatcher = threading.Thread(target=build_watcher, args=("./functions/" + name + "/build.log", name))
    buildWatcher.start()
    
    try:
        command = "./functions/" + name + "/build.sh ./functions/" + name + "/"
        with open("./functions/" + name + "/build.log",'w+') as f:
            proc = subprocess.Popen( command.split(), bufsize=-1, stdout=f, stderr=subprocess.PIPE)
        o, e = proc.communicate()

        command = "./functions/" + name + "/publish.sh ./functions/" + name + "/"
        with open("./functions/" + name + "/build.log",'a') as f:
            proc = subprocess.Popen( command.split(), bufsize=-1, stdout=f, stderr=subprocess.PIPE)
        o, e = proc.communicate()

    except Exception as e:
        print("An exception occurred: " + str(e))
    
    stop_threads[name] = True
    
    
def reconfigure(function, config):
    name = function.__name__
    functionData = {}
    if os.path.exists("./functions/" + name + "/.faaset.json"):
        functionData = json.load(open("./functions/" + name + "/.faaset.json"))
    else:
        print("Unknown function! " + name)
        
    # Use previous config as default
    defaultConfig = functionData["config"]    
    
    # Override default values if config is provided.
    for key in defaultConfig.keys():
        if key not in config:
            config[key] = defaultConfig[key]
    config['function_name'] = name

    # Update function file...
    functionData["config"] = config
    
    # save json file
    json.dump(functionData, open("./functions/" + name + "/.faaset.json", "w"), indent=4)
    
    with open("./functions/" + name + "/config.json", 'w') as json_file:
        json.dump(config, json_file, indent=4)
    
    # Run publish.sh
    global stop_threads
    
    stop_threads[name] = False
    buildWatcher = threading.Thread(target=build_watcher, args=("./functions/" + name + "/build.log", name))
    buildWatcher.start()
    
    try:
        command = "./functions/" + name + "/publish.sh ./functions/" + name + "/"
        with open("./functions/" + name + "/build.log",'w+') as f:
            proc = subprocess.Popen( command.split(), bufsize=-1, stdout=f, stderr=subprocess.PIPE)
        o, e = proc.communicate()

    except Exception as e:
        print("An exception occurred: " + str(e))
    
    stop_threads[name] = True

def source_processor(source, functionName, references):
    source = source.replace("def " + functionName, "\"\"\"\n\ndef yourFunction")
    source = source.replace(functionName + "(", "yourFunction(")
    source = "\"\"\" AUTOMATICALLY COMMENTED OUT BY FaaSET \n" + source
    
    if (len(references) > 0):
        source = "# AUTOMATICALLY ADDED:\nimport json\nimport boto3\nclient=boto3.client(\'lambda\')\n" + source
        for reference in references:
            childFunctionName = reference.__name__
            source += """
#AUTOMATICALLY GENERATED:
def {childFunctionName}(request, context):
    response = client.invoke(FunctionName=\'{childFunctionName}\', InvocationType = \'RequestResponse\', Payload = json.dumps(request))
    return json.load(response[\'Payload\'])""".format(childFunctionName=childFunctionName)
    return source

def progress_watcher(runs, iterations, memSettings, name):
    maxValues = runs * iterations * memSettings
    p_bar = tqdm(total=maxValues, smoothing=True)
    currentPercent = 0
    currentProgress = 0
    while(True):
        global stop_threads
        if (stop_threads[name]):
            p_bar.update(n=round(maxValues - currentProgress))
            p_bar.clear()
            break
        try:
            progress = open(".progress.txt", "r")
            percent = int(progress.read())
            progress.close()
            if (percent > currentPercent):
                diff = (percent - currentPercent) / 100
                currentProgress += diff * runs
                p_bar.update(n=round(diff * runs))
                currentPercent = percent
            elif (percent < currentPercent):
                diff = ((percent + 100) - currentPercent) / 100
                currentProgress += diff * runs
                p_bar.update(n=round(diff * runs))
                currentPercent = percent
        except:
            pass
        time.sleep(0.5)
    return None


def build_watcher(file_name, name):
    consoleContents = ""
    while(True):
        global stop_threads
        if (stop_threads[name]):
            try:
                progress = open(file_name, "r")
                data = progress.read()
                progress.close()
                printData = data.replace(consoleContents, "")
                if (printData != ""):
                    print(printData, end="")
                consoleContents = data
            except:
                pass
            break
        try:
            progress = open(file_name, "r")
            data = progress.read()
            progress.close()
            printData = data.replace(consoleContents, "")
            if (printData != ""):
                print(printData, end="")
            consoleContents = data
        except:
            pass
        time.sleep(0.25)
    return None
