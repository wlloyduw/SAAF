#
# Call a FaaS function many time in parallel or sequentially. Based upon the original partest.sh script.
#
# @author Robert Cordingly
# @author Wes Lloyd
# 
import random
import time
from decimal import Decimal
from threading import Thread
import FaaSET
import pandas as pd
import numpy as np
import os
import json

# Results of calls will be placed into this array.
run_results = []

#
# Called after a request is made, appends extra data to the payload.
#
def callPostProcessor(response, thread_id, run_id, payload, roundTripTime):
    try:
        response['threadID'] = thread_id
        response['runID'] = run_id
        response['roundTripTime'] = roundTripTime
        response['payload'] = payload

        if 'runtime' in response:
            response['latency'] = round(roundTripTime - int(response['runtime']), 2)
        
        if 'cpuType' in response and 'cpuModel' in response:
            response['cpuType'] = response['cpuType'] + " - Model " + str(response['cpuModel'])

        if 'version' in response:
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
        startTime = time.time()
        response = FaaSET.test(function=function, payload=payload, outPath=experiment_name, quiet=True, tags=tags)
        timeSinceStart = round((time.time() - startTime) * 100000) / 100
        callPostProcessor(response, thread_id, i, payload, timeSinceStart)

#
# Run a partest with multiple functions and an experiment all functions will be called concurrently.
#
def experiment(function, threads=1, runs_per_thread=1, payloads=[{}], experiment_name="default", tags={}):

    global run_results
    run_results = []

    random.seed(42)

    # Duplicate payloads so that the number of payloads >= number of runs.
    # Shuffle if needed.
    payloadList = payloads
    while (len(payloadList) < threads * runs_per_thread):
        payloadList += payloads
    if (True):
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


def load(function, experiment, tags={}):
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