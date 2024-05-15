#
# Call a FaaS function many time in parallel or sequentially. Based upon the original partest.sh script.
#
# @author Robert Cordingly
# @author Wes Lloyd
# 
import random
import collections
import time
from decimal import Decimal
from threading import Thread
import FaaSET
import pandas as pd
import numpy as np
import os
import json
import requests
import uuid

# Results of calls will be placed into this array.
run_results = []

#
# Called after a request is made, appends extra data to the payload.
#
def callPostProcessor(response, thread_id, run_id, payload):
    try:
        response['threadID'] = thread_id
        response['runID'] = run_id
        run_results.append(response)
        print("Run " + str(thread_id) + "." + str(run_id) + " successful.")
        return response

    except Exception as e:
        if (response == None):
            print("Run " + str(thread_id) + "." +
                str(run_id) + " Failed with exception: " + str(e)) + ".\nNo response."
        else:
            print("Run " + str(thread_id) + "." +
                str(run_id) + " Failed with exception: " + str(e) + ".\nRequest Response: " + str(response))
        return {}

#
# Define a function to be called by each thread.
#
def callThread(thread_id, runs, function, myPayloads, experiment_name, tags):
    for i in range(0, runs): 
        payload = myPayloads[i]
        print("Call Payload: " + str(payload))
        response = None
        response = FaaSET.test(function=function, payload=payload, outPath=experiment_name, quiet=True, tags=tags)
        callPostProcessor(response, thread_id, i, payload)
        
        
def callProcess(http_endpoint, runs, myPayloads):
    for i in range(0, runs): 
        response = None
        try:
            startTime = time.time()
            response = requests.post(http_endpoint, json=myPayloads[i])
            obj = response.json()
            obj["callStartTime"] = startTime
            obj["callEndTime"] = time.time()
            obj["payload"] = myPayloads[i]
            run_results.append(obj)
        except Exception as e:
            print("Error making request: " + str(e))
            # Print stack trace
            import traceback
            traceback.print_exc()
            
            response = None

#
# Run a partest with multiple functions and an experiment all functions will be called concurrently.
#
def experiment(function, 
               threads=1, 
               runs_per_thread=1, 
               payloads=[{}], 
               shuffle_payloads=True,
               experiment_name="default", 
               tags={}):

    global run_results
    run_results = []

    random.seed(42)

    # Duplicate payloads so that the number of payloads >= number of runs.
    # Shuffle if needed.
    payloadList = payloads
    while (len(payloadList) < threads * runs_per_thread):
        payloadList += payloads
    if (shuffle_payloads):
        random.shuffle(payloadList)

    # Create threads and distribute payloads to threads.
    payloadIndex = 0
    try:
        threadList = []
        for i in range(0, threads):
            payloadsForThread = []
            while (len(payloadsForThread) < runs_per_thread):
                payloadsForThread.append(payloadList[payloadIndex])
                payloadIndex += 1

            thread = Thread(target=callThread, args=(i, runs_per_thread, function, payloadsForThread, experiment_name, tags))
            thread.start()
            threadList.append(thread)
        for i in range(len(threadList)):
            threadList[i].join()
    except Exception as e:
        print("Error making request: " + str(e))

    if len(run_results) == 0:
        print ("ERROR - ALL REQUESTS FAILED")
        return None
    
    try:
        return pd.DataFrame(run_results)
    except Exception:
        return run_results


def fast_experiment(http_endpoint, 
                    processes, 
                    runs_per_process, 
                    payloads=[{}], 
                    shuffle_payloads=True,
                    experiment_name="fast_experiment", 
                    start_delay=5,
                    end_delay=5,
                    tags={}):
    global run_results
    run_results = []
    
    random.seed(42)

    # Duplicate payloads so that the number of payloads >= number of runs.
    # Shuffle if needed.
    payloadList = []
    i = 0
    while (len(payloadList) < processes * runs_per_process):
        payloadList.append(payloads[i % len(payloads)])
        i += 1
    
    if (shuffle_payloads):
        random.shuffle(payloadList)
        
    child_processes = []
    child_index = 0
    
    # if ./fast_experiment does not exist, create it
    if not os.path.isdir("./functions/fast_experiment"):
        os.mkdir("./functions/fast_experiment")
    if not os.path.isdir("./functions/fast_experiment/experiments"):
        os.mkdir("./functions/fast_experiment/experiments")
    if not os.path.isdir("./functions/fast_experiment/experiments/" + experiment_name):
        os.mkdir("./functions/fast_experiment/experiments/" + experiment_name)
    
    # Calculate the start time in ms which is the current time in ms + start_delay
    start_time = time.time() + start_delay
    
    for i in range(processes):
        child_pid = os.fork()
        if child_pid == 0:
            myList = payloadList[child_index:child_index+runs_per_process]
            time.sleep(start_delay * 0.75)
            while time.time() < start_time:
                continue
            callProcess(http_endpoint, runs_per_process, myList)
            time.sleep(end_delay)
            
            # Save all runs
            for run in run_results: 
                run['roundTripTime'] = (run['callEndTime'] * 1000) - (run['callStartTime'] * 1000)
                run['latency'] = run['roundTripTime'] - run['runtime']
                json.dump(run, open("./functions/fast_experiment/experiments/" + experiment_name + "/" + str(uuid.uuid4()) + ".json", "w"), indent=4)
            
            time.sleep(end_delay)
            os._exit(0)
        else:
            child_processes.append(child_pid)
            child_index += runs_per_process
            
    for child_pid in child_processes:
        os.waitpid(child_pid, 0)
        
    time.sleep(end_delay)
    
    return load("fast_experiment", experiment_name, tags)

def load(function, experiment, tags={}):
    name = function
    if (isinstance(function, collections.Callable)):
        name = function.__name__
    
    path = "./functions/" + name + "/experiments/" + experiment + "/"
    jsonList = []
    
    # loop through each json file in path
    folder = os.scandir(path)
    for file in folder:
        with open(path + file.name) as json_file:
            data = json.load(json_file)
            
            # Apply tags
            for key in tags:
                data[key] = tags[key]
            
            jsonList.append(data)
    return pd.DataFrame(jsonList)