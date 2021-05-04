
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
from tqdm.notebook import tqdm, trange

from IPython.display import clear_output, display, HTML, IFrame, FileLink

class Platform(Enum):
    AWS = 1
    GCF = 2
    IBM = 3
    AZURE = 4

lastHash = ""
functionHashes = {}
functionPlatforms = {}
client = boto3.client('lambda')
stop_threads = False

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

def cloud_function(platforms, memory, config, references=[]):
    def decorated(f):
        def wrapper(*args, **kwargs):
            results = f(*args, **kwargs)
            functionName = f.__name__
            wrapper.__name__ = functionName
            functionPlatforms[functionName] = platforms
            source = source_processor(inspect.getsource(f), functionName, references)
            config['functionName'] = functionName
            deploy(functionName, source, platforms, memory, config)
            return results
        return wrapper
    return decorated

def source_processor(source, functionName, references):
    source = source.replace(functionName, "yourFunction")
    source = source.replace("@cloud_function", "#cloud_function")
    
    if (len(references) > 0 or "#CLOUDCALL" in source):
        source = "import json\nimport boto3\nclient=boto3.client(\'lambda\')\n" + source
        lines = source.split("\n")
        for line in lines:
            line = line.strip()
            if "#CLOUDCALL" in line:
                params = line.split(" ")
                childFunctionName = params[1]
                source += """
def {childFunctionName}(request, context):
    response=client.invoke(FunctionName=\'{childFunctionName}\',InvocationType=\'RequestResponse\',Payload=json.dumps(request))
    return(json.load(response[\'Payload\']))""".format(childFunctionName=childFunctionName)
        for reference in references:
            childFunctionName = reference.__name__
            source += """
def {childFunctionName}(request, context):
    response=client.invoke(FunctionName=\'{childFunctionName}\',InvocationType=\'RequestResponse\',Payload=json.dumps(request))
    return(json.load(response[\'Payload\']))""".format(childFunctionName=childFunctionName)
    
    return source

def deploy(name, source, platforms, memory, config):
    sourceHash = hash(source)
    if (name in functionHashes and functionHashes[name] == sourceHash):
        return None

    # Write the handler
    textfile = open("handler_" + name + ".py", "w")
    textfile.write(source)
    textfile.close()

    # Write the config
    for key in config:
        defaultConfig[key] = config[key]
    defaultConfig['handlerFile'] = "handler_" + name + ".py"
    
    with open('../deploy/' + name + '_config.json', 'w') as json_file:
        json.dump(defaultConfig, json_file)

    # Run publish.sh
    threads = []
    for platform in platforms:
        threads.append(threading.Thread(target=deploy_to, args=(platform, name, memory,)))
        #deploy_to(platform, name, memory)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
            
    functionHashes[name] = sourceHash
    
def deploy_to(platform, name, memory):
    if (platform == platform.AWS):
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
        
def test(function, payload, config):
    function(payload, None)
    
    functionName = function.__name__
    
    if (functionName not in functionPlatforms):
        print("Function not found.")
        return None
    
    config["functionName"] = functionName
    config["test"] = payload
    
    for key in config:
        defaultConfig[key] = config[key]
        
    with open('../deploy/' + functionName + '_config.json', 'w') as json_file:
        json.dump(defaultConfig, json_file)
    
    threads = []
    for platform in functionPlatforms[functionName]:
        threads.append(threading.Thread(target=call_on, args=(functionName, platform,)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
        
        
def call_on(functionName, platform):
    if (platform == platform.AWS):
        command = "../deploy/test.sh 1 0 0 0 512 " + functionName + "_config.json"
        print(subprocess.check_output(command.split()).decode('ascii'))
    elif (platform == platform.GCF):
        command = "../deploy/test.sh 0 1 0 0 512 " + functionName + "_config.json"
        print(subprocess.check_output(command.split()).decode('ascii'))
    elif (platform == platform.IBM):
        command = "../deploy/test.sh 0 0 1 0 512 " + functionName + "_config.json"
        print(subprocess.check_output(command.split()).decode('ascii'))
    elif (platform == platform.AZURE):
        command = "../deploy/test.sh 0 0 0 1 512 " + functionName + "_config.json"
        print(subprocess.check_output(command.split()).decode('ascii'))

def progress_watcher():
    p_bar = tqdm(total=100, smoothing=True)
    currentPercent = 0
    while(True):
        global stop_threads
        if (stop_threads):
            p_bar.update(n=100-currentPercent)
            p_bar.clear()
            break
        try:
            progress = open(".progress.txt", "r")
            percent = int(progress.read())
            progress.close()
            if (percent > currentPercent):
                p_bar.update(n=percent-currentPercent)
                currentPercent = percent
            elif (percent < currentPercent):
                currentPercent = percent
                p_bar.reset(total=100)
                p_bar.update(n=percent)
        except:
            pass
        time.sleep(0.5)

def run_experiment(function, experiment, config, platform):
    
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
    
    with open('../../test/experiments/interactiveExperiment.json', 'w') as json_file:
        json.dump(experiment, json_file)
        
    currentPath = pathlib.Path().absolute()
    os.chdir("../../test")
    try:
        shutil.rmtree("history/interactiveExperiment")
    except:
        pass
    
    progressWatcher = threading.Thread(target=progress_watcher)
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