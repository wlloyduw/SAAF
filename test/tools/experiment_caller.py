#!/usr/bin/env python3

#
# Call a FaaS function many time in parallel or sequentially. Based upon the original partest.sh script.
#
# @author Wes Lloyd
# @author Robert Cordingly
#
import ast
import datetime
import json
import os
import random
import requests
import subprocess
import sys
import time
from decimal import Decimal
from threading import Thread
from pipeline_transition import transition_function

# Results of calls will be placed into this array.
run_results = []

#
# Make a call using AWS CLI
#
def callAWS(function, payload, callAsync):
    cmd = ['aws', 'lambda', 'invoke', '--invocation-type', 'RequestResponse', '--cli-read-timeout', 
           '450', '--function-name', str(function['endpoint']), '--payload', payload, '/dev/stdout']
    if (callAsync):
        cmd = ['aws', 'lambda', 'invoke', '--invocation-type', 'Event', '--cli-read-timeout', 
               '450', '--function-name', str(function['endpoint']), '--payload', '"' + payload + '"', '/dev/stdout']
    proc = subprocess.Popen( cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = proc.communicate()
    print("STDOUT: " + str(o.decode('ascii')) + "\nSTDERR: " + str(e.decode('ascii')))

    if (callAsync):
        return '{"RESPONSE": "USE S3 PULL TO RETRIEVE RESPONSES", "version":42}'
    return str(o.decode('ascii')).split('\n')[0][:-1]

#
# Make a call using Google CLI
#
def callGoogle(function, payload):
    cmd = ['gcloud', 'functions', 'call', str(function['endpoint']), '--data', payload]
    proc = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = proc.communicate()
    print("STDOUT: " + str(o.decode('ascii')) + "\nSTDERR: " + str(e.decode('ascii')))
    return str(o.decode('ascii')).replace('\n', '')[34:-1]

#
# Make a call using IBM CLI
#
def callIBM(function, payload):
    cmd = ['ibmcloud', 'fn', 'action', 'invoke', '--result', str(function['endpoint'])]
    jsonDict = ast.literal_eval(payload)
    for key in jsonDict:
        cmd.append('-p')
        cmd.append(str(key))
        cmd.append(str(jsonDict[key]))
    proc = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = proc.communicate()
    print("STDOUT: " + str(o.decode('ascii')) + "\nSTDERR: " + str(e.decode('ascii')))
    return str(o.decode('ascii'))

#
# Make a call using a regular HTTP request
#
def callHTTP(function, payload):
    response = requests.post(function['endpoint'], data=json.dumps(
        payload), headers={'content-type': 'application/json'})
    print("Response: " + str(response.text))
    return response.text

#
# Called after a request is made, appends extra data to the payload.
#
def callPostProcessor(function, response, thread_id, run_id, payload, roundTripTime):
    try:
        dictionary = ast.literal_eval(response)
        dictionary['2_thread_id'] = thread_id
        dictionary['1_run_id'] = run_id
        dictionary['zAll'] = "Final Results:"
        dictionary['roundTripTime'] = roundTripTime
        dictionary['payload'] = str(payload)

        if 'runtime' in dictionary:
            dictionary['latency'] = round(roundTripTime - int(dictionary['runtime']), 2)

        if 'cpuType' in dictionary and 'cpuModel' in dictionary:
            dictionary['cpuType'] = dictionary['cpuType'] + " - Model " + str(dictionary['cpuModel'])

        if (len(function)) > 1 and 'platform' not in dictionary:
            dictionary['endpoint'] = function['endpoint']

        if 'version' in dictionary:
            run_results.append(dictionary)

        key_list = list(dictionary.keys())
        for key in key_list:
            value = str(dictionary[key])
            dictionary[key] = str(dictionary[key]).replace(
                ',', ';').replace('\t', '\\t').replace('\n', '\\n')

        print("Run " + str(thread_id) + "." + str(run_id) + " successful.")

        return dictionary

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
def callThread(thread_id, runs, function, exp, myPayloads):
    callAsync = exp['callAsync']

    for i in range(0, runs): 

        callPayload = myPayloads[i]
        print("Call Payload: " + str(callPayload))

        startTime = 0
        response = None

        # Format payload for CLIs.
        payload = str(json.dumps(callPayload))

        startTime = time.time()
        platform = function['platform']
        response = ""

        # Make call depending on platform.
        if (platform == 'HTTP' or platform == 'Azure'):
            response = callHTTP(function, payload)
        elif (platform == 'AWS Lambda'):
            response = callAWS(function, payload, callAsync)
        elif (platform == 'Google'):
            response = callGoogle(function, payload)
        elif (platform == 'IBM'):
            response = callIBM(function, payload)

        timeSinceStart = round((time.time() - startTime) * 100000) / 100

        callPostProcessor(function, response, thread_id, i, payload, timeSinceStart)

#
# Define a pipeline to be called by each thread.
#
def callPipelineThread(thread_id, seqIterations, functions, experiments, myPayloads):

    for j in range(0, seqIterations): 

        passOn = {}

        i = 0
        while (i >= 0 and i < len(functions) and i is not None):
            function = functions[i]
            exp = experiments[i]
            callPayload = myPayloads[i + (j * seqIterations)]

            callAsync = exp['callAsync']

            startTime = 0
            response = None

            # Format payload for pipeline.
            if (exp['passPayloads']):
                lastPayload = callPayload
                for transition in list(exp['transitions'].keys()):
                    if transition in passOn:
                        lastPayload[str(exp['transitions'][transition])] = passOn[transition]

                callPayload = {**passOn, **lastPayload}
                payload = str(json.dumps(callPayload))
            else:
                payload = str(json.dumps(callPayload))
                
            print("Call Function: " + str(function))
            print("Call Payload: " + str(callPayload))

            startTime = time.time()
            platform = function['platform']
            response = ""

            # Make call depending on platform.
            if (platform == 'HTTP' or platform == 'Azure'):
                response = callHTTP(function, payload)
            elif (platform == 'AWS Lambda'):
                response = callAWS(function, payload, callAsync)
            elif (platform == 'Google'):
                response = callGoogle(function, payload)
            elif (platform == 'IBM'):
                response = callIBM(function, payload)

            timeSinceStart = round((time.time() - startTime) * 100000) / 100

            passOn = callPostProcessor(function, response, thread_id, j, payload, timeSinceStart)

            i = transition_function(i, functions, experiments, myPayloads, passOn)

#
# Run a partest with multiple functions and an experiment all functions will be called concurrently.
#
def callExperiment(functionList, exp):

    print("\n-----------------------------------------------------------------")
    print("CREATING AND RUNNING THREADS FOR EXPERIMENT")
    print("-----------------------------------------------------------------\n")

    threads = exp['threads']
    total_runs = exp['runs']
    runs_per_thread = int(total_runs / threads)
    payload = exp['payloads']
    useCLI = exp['callWithCLI']
    randomSeed = exp['randomSeed']
    shufflePayloads = exp['shufflePayloads']
    random.seed(randomSeed)

    function_calls = []
    for i in range(0, len(functionList)):
        func = functionList[i]
        if useCLI:
            function_calls.append({
                'platform': func['platform'],
                'endpoint': func['function']
            })
        else:
            function_calls.append({
                'platform': "HTTP",
                'endpoint': func['endpoint']
            })

    # Duplicate payloads so that the number of payloads >= number of runs.
    # Shuffle if needed.
    payloadList = payload
    while (len(payloadList) < total_runs):
        payloadList += payload
    if (shufflePayloads):
        random.shuffle(payloadList)

    #
    # Create threads and distribute payloads to threads.
    #
    payloadIndex = 0
    try:
        threadList = []
        for i in range(0, threads):
            for j in range(len(function_calls)):

                payloadsForThread = []
                while (len(payloadsForThread) < runs_per_thread):
                    payloadsForThread.append(payloadList[payloadIndex])
                    payloadIndex += 1

                thread = Thread(target=callThread, args=(i, runs_per_thread, function_calls[j], exp, payloadsForThread))
                thread.start()
                threadList.append(thread)
        for i in range(len(threadList)):
            threadList[i].join()
    except Exception as e:
        print("Error making request: " + str(e))

    #
    # Print results of each run.
    #
    if len(run_results) == 0:
        print ("ERROR - ALL REQUESTS FAILED")
        return None
    
    return run_results

#
# Run a pipeline of multiple functions and experiments.
# The first experiment will be used as the "master" experiment
# to define number of threads and runs. Payloads and other data
# will be pulled from each other payload file. 
#
# Pipelines can only execute linearly in the order that function
# and experiment files are provided in the arrays.
#
def callPipelineExperiment(functionList, experimentList):

    print("\n-----------------------------------------------------------------")
    print("CREATING AND RUNNING THREADS FOR PIPELINE (experiment_caller.py)")
    print("-----------------------------------------------------------------\n")

    if (len(functionList) != len(experimentList)):
        print("ERROR! For pipelines an equal number of experiments and functions must be provided!")
        return None

    # Get values from master experiment file.
    threads = experimentList[0]['threads']
    total_runs = experimentList[0]['runs']
    useCLI = experimentList[0]['callWithCLI']
    randomSeed = experimentList[0]['randomSeed']
    seqIterations = int(total_runs / threads)

    pipelineLength = len(functionList)

    # Preprocess Endpoints...
    function_calls = []
    for i in range(0, len(functionList)):
        func = functionList[i]
        if useCLI:
            function_calls.append({
                'platform': func['platform'],
                'endpoint': func['function']
            })
        else:
            function_calls.append({
                'platform': "HTTP",
                'endpoint': func['endpoint']
            })

    random.seed(randomSeed)

    #
    # Create threads and distribute payloads to threads.
    #
    payloadIndex = 0
    try:
        threadList = []
        for i in range(0, threads):

            globalPayloadList = []

            for x in range(0, seqIterations):
                for j in range(0, len(experimentList)):
                    tempPayloadList = experimentList[j]['payloads']
                    shufflePayloads = experimentList[j]['shufflePayloads']

                    # Duplicate payloads so that the number of payloads >= number of runs.
                    # Shuffle if needed.
                    payloadList = tempPayloadList
                    while (len(payloadList) < total_runs):
                        payloadList += tempPayloadList
                    if (shufflePayloads):
                        random.shuffle(payloadList)

                    globalPayloadList.append(payloadList[0])

            thread = Thread(target=callPipelineThread, args=(i, seqIterations, function_calls, experimentList, globalPayloadList))
            thread.start()
            threadList.append(thread)
        for i in range(len(threadList)):
            threadList[i].join()
    except Exception as e:
        print("Error making request: " + str(e))

    #
    # Print results of each run.
    #
    if len(run_results) == 0:
        print ("ERROR - ALL REQUESTS FAILED")
        return None
    
    return run_results