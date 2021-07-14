
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
from tqdm.notebook import tqdm, trange

from IPython.display import clear_output, display, HTML, IFrame, FileLink
from IPython.display import JSON

class Platform(Enum):
    AWS = 1
    GCF = 2
    IBM = 3
    AZURE = 4

lastHash = ""
functionHashes = {}
functionRequirements = {}
functionPlatforms = {}
client = boto3.client('lambda')
stop_threads = False
deployFunctions = True

startPath = pathlib.Path().absolute()

defaultConfig = {
	"README": "See ./deploy/README.md for help!",
	"lambdaHandler": "lambda_function.lambda_handler",
    "handlerFile": "handler.py",
	"lambdaRoleARN": "",
	"lambdaSubnets": "",
	"lambdaSecurityGroups": "",
	"lambdaEnvironment": "Variables={EXAMPLEVAR1=VAL1,EXAMPLEVAR2=VAL2}",
	"lambdaRuntime": "python3.7",
	"googleHandler": "hello_world",
	"googleRuntime": "python37",
	"ibmRuntime": "python:3",
	"azureRuntime": "python",
    "test": {}
}

def cloud_function(platforms, memory, config, references=[], requirements=None, containerize=False, deploy=True):
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
    """
    def decorated(f):
        def wrapper(*args, **kwargs):
            results = f(*args, **kwargs)
            functionName = f.__name__
            wrapper.__name__ = functionName
            functionPlatforms[functionName] = platforms
            source = source_processor(inspect.getsource(f), functionName, references)
            config['functionName'] = functionName
            global deployFunctions
            if deployFunctions and deploy:
                deploy_function(functionName, source, platforms, memory, config, requirements, containerize)
            return results
        return wrapper
    return decorated

def setDeploy(doDeploy):
    """Sets function deployment on a global scope. Useful if you want to write
        a bunch of functions locally before deploying to the cloud.

    Args:
        doDeploy ([type]): Whether if you want your functions to be deployed.
    """
    global deployFunctions 
    deployFunctions = doDeploy
    
def test(function, payload, config):
    """ Executes a function locally and then executes it on the cloud. If the function is deployed to multiple 
        platforms the function will be executed on all platforms in parallel. Function output is printed to the
        console.
        
        If the function is only deployed to a single platform this function will return the results of the 
        request in either a dictionary (AWS) or string (all others) dependending on the platform.

    Args:
        function (method): The cloud function to execute.
        payload (obj): The request payload object.
        config (obj): Context object to supply other required parameters to the function such as Lambda ARNs.
    Returns:
        obj or string: Function response payload, either as a dictionary object or string depending on the platform
    """
    
    print("Running local test...", end=" ")
    function(payload, None)
    print("Success! Testing on cloud...")
    
    functionName = function.__name__
    
    if (functionName not in functionPlatforms):
        print("Function not found: " + str(functionName))
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
        return call_on(functionName, functionPlatforms[functionName][0])

def run_experiment(function, experiment, config, platform):
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
    
    global startPath
    os.chdir(startPath)
    data = None
    functionName = function.__name__
    global stop_threads
    stop_threads = False
    
    if (platform == platform.AWS):
        function = {
            "function": functionName,
            "platform": "AWS Lambda",
            "source": "../python_template",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    elif (platform == platform.IBM):
        function = {
            "function": functionName,
            "platform": "IBM",
            "source": "../python_template",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    elif (platform == platform.GCF):
        function = {
            "function": functionName,
            "platform": "Google",
            "source": "../python_template",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    elif (platform == platform.AZURE):
        function = {
            "function": functionName,
            "platform": "Azure",
            "source": "../python_template",
            "endpoint": ""
        }
        with open('../../test/functions/interactiveFunction.json', 'w') as json_file:
            json.dump(function, json_file)
    
    # Set default values
    experiment["outputGroups"] = []
    experiment["ignoreFromGroups"] = []
    experiment["ignoreByGroup"] = {}
    experiment["combineSheets"] = True
    
    with open('../../test/experiments/interactiveExperiment.json', 'w') as json_file:
        json.dump(experiment, json_file)
        
    currentPath = pathlib.Path().absolute()
    os.chdir("../../test")
    try:
        shutil.rmtree("history/interactiveExperiment")
    except:
        pass
    
    progressWatcher = threading.Thread(target=progress_watcher, args=(experiment['runs'], experiment['iterations'],))
    progressWatcher.start()
    
    try:
        command = "./faas_runner.py -f functions/interactiveFunction.json -e experiments/interactiveExperiment.json -o history/interactiveExperiment"
        data = subprocess.check_output(command.split()).decode('ascii')
        csvReport = glob("history/interactiveExperiment/*.csv")[0]
        
        command = "./tools/report_splitter.py " + csvReport
        subprocess.check_output(command.split()).decode('ascii')
        
        reportPath = csvReport.replace(".csv", "") + " - split"
        data = pd.read_csv(reportPath + "/Raw results of each run.csv")
    except Exception as e:
        print(e)
    
    stop_threads = True
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
    if (platform == platform.AWS):
        if (containerize):
            print("Building " + name + " container for AWS Lambda. Container deployments take longer and do not immediately destroy infrastructure.")
            command = "../deploy/build.sh 1 0 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/aws-log.txt"
            print("Running this command:\n" + command)
            subprocess.check_output(command.split()).decode('ascii')
        else:
            print("Deploying " + name + " to AWS Lambda...")
            command = "../deploy/publish.sh 1 0 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/aws-log.txt"
            subprocess.check_output(command.split()).decode('ascii')
        print("Deployment to AWS Lambda Complete!")
    elif (platform == platform.GCF):
        print("Deploying " + name + " to GCF...")
        command = "../deploy/publish.sh 0 1 0 0 " + str(memory) + " " + name + "_config.json > ../deploy/gcf-log.txt"
        subprocess.check_output(command.split()).decode('ascii')
        print("Deployment to Google Cloud Functions Complete!")
    elif (platform == platform.IBM):
        print("Deploying " + name + " to IBM...")
        command = "../deploy/publish.sh 0 0 1 0 " + str(memory) + " " + name + "_config.json > ../deploy/ibm-log.txt"
        subprocess.check_output(command.split()).decode('ascii')
        print("Deployment to IBM Cloud Functions Complete!")
    elif (platform == platform.AZURE):
        print("Deploying " + name + " to Azure...")
        command = "../deploy/publish.sh 0 0 0 1 " + str(memory) + " " + name + "_config.json > ../deploy/azure-log.txt"
        subprocess.check_output(command.split()).decode('ascii')
        print("Deployment to Azure Functions Complete!")


def call_on(functionName, platform):
    try:
        if (platform == platform.AWS):
            command = "../deploy/test.sh 1 0 0 0 512 " + functionName + "_config.json"
            out = subprocess.check_output(command.split()).decode('ascii')
            obj = json.loads(out.split("\n")[1][:-1])
            print(json.dumps(obj, indent=4))
            return obj
            #print(subprocess.check_output(command.split()).decode('ascii'))
        elif (platform == platform.GCF):
            command = "../deploy/test.sh 0 1 0 0 512 " + functionName + "_config.json"
            out = subprocess.check_output(command.split()).decode('ascii')
            print(out)
            return out
        elif (platform == platform.IBM):
            command = "../deploy/test.sh 0 0 1 0 512 " + functionName + "_config.json"
            out = subprocess.check_output(command.split()).decode('ascii')
            print(out)
            return out
        elif (platform == platform.AZURE):
            command = "../deploy/test.sh 0 0 0 1 512 " + functionName + "_config.json"
            out = subprocess.check_output(command.split()).decode('ascii')
            print(out)
            return out
    except Exception as e:
        print("FaaS call failed! For container based function it may not be available yet. Error: " + str(e))
        return ""


def progress_watcher(runs, iterations):
    maxValues = runs * iterations
    p_bar = tqdm(total=runs * iterations, smoothing=True)
    currentPercent = 0
    currentProgress = 0
    while(True):
        global stop_threads
        if (stop_threads):
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