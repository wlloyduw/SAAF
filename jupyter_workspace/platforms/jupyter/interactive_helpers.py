
import pandas as pd
import numpy as np
import json
import os
import boto3
import ast
from enum import Enum
import subprocess
import pathlib
from glob import glob
import shutil
import inspect
import threading
import time
import math
import uuid
from tqdm.notebook import tqdm, trange

from IPython.display import clear_output, display, HTML, IFrame, FileLink
from IPython.display import JSON

class Platform(Enum):
    AWS = 1
    GCF = 2
    IBM = 3
    AZURE = 4
    DOCKER = 5
    
class RunMode(Enum):
    LOCAL = 1
    CLOUD = 2
    NONE = 3

lastHash = ""
functionHashes = {}
functionRequirements = {}
functionPlatforms = {}
client = boto3.client('lambda')
stop_threads = {}
globalDeploy = True
globalConfig = None

startPath = pathlib.Path().absolute()

defaultConfig = {
	"README": "See ./deploy/README.md for help!",
	"lambdaHandler": "lambda_function.lambda_handler",
    "handlerFile": "handler.py",
	"lambdaRoleARN": "",
	"lambdaSubnets": "",
	"lambdaSecurityGroups": "",
	"lambdaEnvironment": "Variables={EXAMPLEVAR1=VAL1,EXAMPLEVAR2=VAL2}",
	"lambdaRuntime": "python3.8",
	"googleHandler": "hello_world",
	"googleRuntime": "python37",
	"ibmRuntime": "python:3",
	"azureRuntime": "python",
    "test": {}
}

def cloud_function(platforms=[Platform.AWS], 
                   memory=256, 
                   config=None, 
                   references=[], 
                   requirements=None, 
                   containerize=False, 
                   deploy=True, 
                   runMode=RunMode.CLOUD):
    """Cloud Function decorator. Using this will turn any Python function into a cloud function and deploy
        automatically to a variety of FaaS platforms. Functions require two arguments, a request and context object.
        Functions are only redeployed when the source code is changed. Cloud functions must first successfully execute
        locally before they are deployed to the cloud.

    Args:
        platforms (list): The platforms you would like to deploy to. Define platforms with the Platform enum.
        memory (int): The memory setting to deploy the function with.
        config (obj): Context object to supply other required parameters to the function such as Lambda ARNs.
        references (list, optional): A list of other cloud functions that this function calls. 
                Other functions will deployed as separate functions. If this function needs to call other
                functions they should be defined within the scope of this function or in a separate file. Defaults to [].
        requirements (string, optional): Can be used to define function dependencies. Add a string in
                requirements.txt format and dependencies will be downloaded before deployed. Defaults to None.
        containerize (bool, optional): Whether the function should be deployed as a Docker container rather than
                zip file. Currently only supported on AWS Lambda. Defaults to False.
        deploy (bool, optional): Whether the function should be automatically deployed when changes are made. 
                Can be used to disable automatic deployment. Defaults to True.
        runMode (enum, optional): The method of executing the function as a standard function call.
                For example if your function is named "hello_world", executing hello_world(request, context)
                in your notenook will result in three different options:
                1. RunMode.LOCAL (default): The method will be executed locally on your computer.
                2. RunMode.CLOUD: The method will be executed on the cloud as a FaaS function. 
                    The request being made will be done behind the scenes.
                3. RunMode.NONE: The method's code will not be executed at all. This can be usedful
                    for just deploying functions that may not work locally.
    """
    global globalDeploy
    global globalConfig
    if config == None:
        config = globalConfig
    
    def decorated(f):
        def wrapper(*args, **kwargs):
            results = None
                
            functionName = f.__name__
            wrapper.__name__ = functionName
            functionPlatforms[functionName] = platforms
            
            if runMode == RunMode.LOCAL:
                results = f(*args, **kwargs)
            
            if globalDeploy and deploy:
                source = source_processor(inspect.getsource(f), functionName, references)
                config['functionName'] = functionName
                deploy_function(functionName, source, platforms, memory, config, requirements, containerize)
            if runMode == RunMode.CLOUD:
                if len(platforms) > 1:
                    print("ERROR: Running functions in cloud mode requires only a single platform to be selected!")
                else:
                    results = test(function=f, payload=args[0], config=config, quiet=True, skipLocal=True)
            return results
        return wrapper
    return decorated

def setGlobalDeploy(deploy):
    """Sets function deployment on a global scope. Useful if you want to write
        a bunch of functions locally before deploying to the cloud.

    Args:
        deploy ([type]): Whether if you want your functions to be deployed.
    """
    global globalDeploy 
    globalDeploy = deploy
    
def setGlobalConfig(config):
    global globalConfig
    globalConfig = config
    
def test(function, payload, config=None, quiet=False, skipLocal=False):
    """ Executes a function locally and then executes it on the cloud. If the function is deployed to multiple 
        platforms the function will be executed on all platforms in parallel. Function output is printed to the
        console. This method ignores the RunMode option of the function, if you do not what your function to
        be executed locally you can enable the skipLocal option.
        
        If the function is only deployed to a single platform this function will return the results of the 
        request in either a dictionary (AWS) or string (all others) dependending on the platform.

    Args:
        function (method): The cloud function to execute.
        payload (obj): The request payload object.
        config (obj, optional): Context object to supply other required parameters to the function such as Lambda ARNs.
        quiet (bool): Whether run information should NOT be printed to the console.
        skipLocal (bool): Whether the local function call should be skipped. Local runs are always skipped with
            functions with CLOUD run mode.
    Returns:
        obj or string: Function response payload, either as a dictionary object or string depending on the platform
    """
    
    global globalConfig
    if config == None:
        config = globalConfig
    
    if not skipLocal or function.__name__ == "wrapper": 
        if not quiet: print("Running local test...")
        function(payload, None)
    if not quiet: print("Testing on cloud...")
    
    functionName = function.__name__
    
    if (functionName not in functionPlatforms):
        print("Error: Function not found: " + str(functionName))
        return None
    
    config["functionName"] = functionName
    config["test"] = payload
    
    for key in config:
        defaultConfig[key] = config[key]
        
    with open('../deploy/' + functionName + '_config.json', 'w') as json_file:
        json.dump(defaultConfig, json_file)
    
    if len(functionPlatforms[functionName]) > 1:
        threads = []
        for platform in functionPlatforms[functionName]:
            threads.append(threading.Thread(target=call_on, args=(functionName, platform,)))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return None
    else:
        return call_on(functionName=functionName, platform=functionPlatforms[functionName][0], quiet=quiet)

def run_experiment(function, experiment, platform=Platform.AWS, config=None):
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
    
    global globalConfig
    if config == None:
        config = globalConfig
    
    global startPath
    os.chdir(startPath)
    data = None
    
    global stop_threads
    stop_threads["experiment"] = False
    
    functionName = function.__name__
    
    exp_id = functionName + "-" + str(uuid.uuid4())
    if 'name' in experiment:
        exp_id = functionName + "-" + experiment['name'] + "-" + str(uuid.uuid4())

    print("Running experiment: " + exp_id)
    
    if (platform == platform.AWS):
        function = {
            "function": functionName,
            "platform": "AWS Lambda",
            "source": "../jupyter_workspace/deploy/" + functionName + "_config.json",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    elif (platform == platform.IBM):
        function = {
            "function": functionName,
            "platform": "IBM",
            "source": "../jupyter_workspace/deploy/" + functionName + "_config.json",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    elif (platform == platform.GCF):
        function = {
            "function": functionName,
            "platform": "Google",
            "source": "../jupyter_workspace/deploy/" + functionName + "_config.json",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    elif (platform == platform.AZURE):
        function = {
            "function": functionName,
            "platform": "Azure",
            "source": "../jupyter_workspace/deploy/" + functionName + "_config.json",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    elif (platform == platform.DOCKER):
        print("Experiments are not supported on the docker platform.")
        return False
    
    # Set default values
    experiment["outputGroups"] = []
    experiment["ignoreFromGroups"] = []
    experiment["ignoreByGroup"] = {}
    experiment["combineSheets"] = True
    
    with open('../../test/experiments/interactiveExperiment.json', 'w') as json_file:
        json.dump(experiment, json_file)
        
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
                    os.system("mv {} {}".format(os.path.join(historyPath, folder, file), os.path.join(historyPath, "combined")))
                try:
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

def deploy_function(name, source, platforms, memory, config, requirements, containerize):
    sourceHash = hash(source)
    if (name in functionHashes and functionHashes[name] == sourceHash):
        return None

    # Write the handler
    textfile = open("handler_" + name + ".py", "w")
    textfile.write(source)
    textfile.close()
    
    # Check or create includes.
    if not os.path.isdir("includes_" + name):
        os.mkdir("includes_" + name)

    # Write the config
    for key in config:
        defaultConfig[key] = config[key]
    defaultConfig['handlerFile'] = "handler_" + name + ".py"
    
    with open('../deploy/' + name + '_config.json', 'w') as json_file:
        json.dump(defaultConfig, json_file)
        
    if (requirements is not None):
        print("Preparing packages...")
        
        if (name not in functionRequirements or functionRequirements[name] != requirements):
            try:
                shutil.rmtree("../deploy/" + name + "_package")
            except:
                pass
        functionRequirements[name] = requirements
            
        # Create Package directory
        if (not os.path.exists("../deploy/" + name + "_package")):
            os.mkdir("../deploy/" + name + "_package")
            pass
        
        # Create requirements.txt
        with open("../deploy/" + name + "_package/requirements.txt", "w") as f:
            f.write(requirements)
        
        # Download dependencies
        command = "python3 -m pip install -r ../deploy/" + name + "_package/requirements.txt --target=../deploy/" + name + "_package"
        subprocess.check_output(command.split()).decode('ascii')

    # Run publish.sh
    threads = []
    for platform in platforms:
        threads.append(threading.Thread(target=deploy_to, args=(platform, name, memory, containerize,)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
            
    functionHashes[name] = sourceHash


def source_processor(source, functionName, references):
    source = source.replace("includes_" + functionName, "INCLUDESPATH")
    source = source.replace("def " + functionName, "\"\"\"\n\ndef yourFunction")
    source = source.replace(functionName + "(", "yourFunction(")
    source = source.replace("INCLUDESPATH", "includes_" + functionName)
    source = source.replace("@cloud_function", "\n\"\"\"AUTOMATICALLY COMMENTED OUT \ncloud_function")
    
    if (len(references) > 0):
        source = "# AUTOMATICALLY ADDED:\nimport json\nimport boto3\nclient=boto3.client(\'lambda\')\n" + source
        lines = source.split("\n")
        for reference in references:
            childFunctionName = reference.__name__
            source += """
#AUTOMATICALLY GENERATED:
def {childFunctionName}(request, context):
    response = client.invoke(FunctionName=\'{childFunctionName}\', InvocationType = \'RequestResponse\', Payload = json.dumps(request))
    return json.load(response[\'Payload\'])""".format(childFunctionName=childFunctionName)
    return source


def deploy_to(platform, name, memory, containerize):
    global stop_threads
    if (platform == platform.AWS):
        
        filename = "../deploy/" + name + "_aws_build_progress.txt"
        try:
            os.remove(filename)
        except Exception as e:
            pass
        stop_threads["aws_build"] = False
        buildWatcher = threading.Thread(target=build_watcher, args=(filename, "aws_build"))
        buildWatcher.start()
        
        if (containerize):
            try:
                command = "../deploy/containerBuild.sh 1 0 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/aws-log.txt"
                subprocess.check_output(command.split()).decode('ascii')
                command = "../deploy/containerPublish.sh 1 0 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/aws-log.txt"
                subprocess.check_output(command.split()).decode('ascii')
            except Exception as e:
                print(e)
        else:
            command = "../deploy/publish.sh 1 0 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/aws-log.txt"
            subprocess.check_output(command.split()).decode('ascii')
        stop_threads["aws_build"] = True
        buildWatcher.join()
        print("Deployment to AWS Lambda Complete!")
    elif (platform == platform.GCF):
        
        filename = "../deploy/" + name + "_gcf_build_progress.txt"
        try:
            os.remove(filename)
        except Exception as e:
            pass
        stop_threads["gcf_build"] = False
        buildWatcher = threading.Thread(target=build_watcher, args=(filename, "gcf_build"))
        buildWatcher.start()
        
        if (containerize):
            print("Building containers is currently not supported on Google Cloud Functions.")
        else:
            try:
                command = "../deploy/publish.sh 0 1 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/gcf-log.txt"
                subprocess.check_output(command.split()).decode('ascii')
            except Exception as e:
                print(e)
        stop_threads["gcf_build"] = True
        buildWatcher.join()
        print("Deployment to Google Cloud Functions Complete!")
    elif (platform == platform.IBM):
        filename = "../deploy/" + name + "_ibm_build_progress.txt"
        try:
            os.remove(filename)
        except Exception as e:
            pass
        stop_threads["ibm_build"] = False
        buildWatcher = threading.Thread(target=build_watcher, args=(filename, "ibm_build"))
        buildWatcher.start()
        
        if (containerize):
            print("Building containers is currently not supported on IBM Cloud Functions.")
        else:
            try:
                command = "../deploy/publish.sh 0 0 1 0 " + str(memory) + " " + name + "_config.json > ../deploy/ibm-log.txt"
                subprocess.check_output(command.split()).decode('ascii')
            except Exception as e:
                print(e)
        stop_threads["ibm_build"] = True
        buildWatcher.join()
        print("Deployment to IBM Cloud Functions Complete!")
    elif (platform == platform.AZURE):
        filename = "../deploy/" + name + "_azure_build_progress.txt"
        try:
            os.remove(filename)
        except Exception as e:
            pass
        stop_threads["azure_build"] = False
        buildWatcher = threading.Thread(target=build_watcher, args=(filename, "azure_build"))
        buildWatcher.start()
        
        
        if (containerize):
            print("Building containers is currently not supported on Google Cloud Functions.")
        else:
            try:
                command = "../deploy/publish.sh 0 0 0 1 " + str(memory) + " " + name + "_config.json > ../deploy/azure-log.txt"
                subprocess.check_output(command.split()).decode('ascii')
            except Exception as e:
                print(e)    
        stop_threads["azure_build"] = True
        buildWatcher.join()
        print("Deployment to Azure Functions Complete!")
    elif (platform == platform.DOCKER):
        filename = "../deploy/" + name + "_aws_build_progress.txt"
        try:
            os.remove(filename)
        except Exception as e:
            pass
        stop_threads["docker_build"] = False
        buildWatcher = threading.Thread(target=build_watcher, args=(filename, "docker_build"))
        buildWatcher.start()
        
        try:
            command = "../deploy/containerBuild.sh 1 0 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/aws-log.txt"
            subprocess.check_output(command.split()).decode('ascii')
        except Exception as e:
            print(e)

        stop_threads["docker_build"] = True
        buildWatcher.join()
        print("Deployment to local Docker instance complete!")

def call_on(functionName, platform, quiet=False):
    try:
        if (platform == platform.AWS):
            command = "../deploy/test.sh 1 0 0 0 512 " + functionName + "_config.json"
            try:
                out = subprocess.check_output(command.split()).decode('ascii')
                obj = json.loads(out.split("\n")[1][:-1])
                if not quiet: print(json.dumps(obj, indent=4))
                return obj
            except Exception as e:
                print("Exception occurred calling function on AWS Lambda: " + str(e))
                return None
        elif (platform == platform.GCF):
            command = "../deploy/test.sh 0 1 0 0 512 " + functionName + "_config.json"
            try:
                out = subprocess.check_output(command.split()).decode('ascii')
                out = out.replace("\n", "")
                obj = json.loads(out[out.index('\'')+1:-1])
                if not quiet: print(out)
                return obj
            except Exception as e:
                print("Exception occurred calling function on Google Cloud Functions: " + str(e))
                return None
        elif (platform == platform.IBM):
            try:
                command = "../deploy/test.sh 0 0 1 0 512 " + functionName + "_config.json"
                out = subprocess.check_output(command.split()).decode('ascii')
                obj = json.loads(out[out.index('{'):])
                if not quiet: print(out)
                return obj
            except Exception as e:
                print("Exception occurred calling function on IBM Cloud Functions: " + str(e))
                return None
        elif (platform == platform.AZURE):
            try:
                command = "../deploy/test.sh 0 0 0 1 512 " + functionName + "_config.json"
                out = subprocess.check_output(command.split()).decode('ascii')
                if not quiet: print(out)
                return out
            except Exception as e:
                print("Exception occurred calling function on Azure Cloud Functions: " + str(e))
                return None
        elif (platform == platform.DOCKER):
            command = "../deploy/containerTest.sh 1 0 0 0 512 " + functionName + "_config.json"
            try:
                out = subprocess.check_output(command.split()).decode('ascii')
                obj = json.loads(out[out.index('{'):])
                if not quiet: print(out)
                return obj
            except Exception as e:
                print("Exception occurred calling function on local Docker: " + str(e))
                return None
    except Exception as e:
        print("FaaS call failed! For container based functions it may not be available yet. Error: " + str(e))
        return {"Error": "An error occurred calling the function."}


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
        time.sleep(0.5)
    return None
