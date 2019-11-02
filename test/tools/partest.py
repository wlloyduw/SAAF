#!/usr/bin/env python3

#
# Call a FaaS function many time in parallel or sequentially. Based upon the original partest.sh script.
#
# @author Wes Lloyd
# @author Robert Cordingly
#

import ast
import boto3
import botocore
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

def parTest(functionList, experiment):
    output = ""

    exp = experiment

    threads = exp['threads']
    total_runs = exp['runs']
    runs_per_thread = int(total_runs / threads)
    payload = exp['payloads']
    useCLI = exp['callWithCLI']

    random.seed(exp['randomSeed'])

    #botocore.config.Config(connect_timeout = 120, read_timeout = 120, max_pool_connections = threads, retries = {'max_attempts': 0})

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

    run_results = []

    #
    # Define a function to be called by each thread.
    #
    def make_call(thread_id, runs, function_call, myPayloads):
        for i in range(0, runs):

            callPayload = myPayloads[i]
            print("Call Payload: " + str(callPayload))

            startTime = 0
            response = None

            # Format payload for CLIs.
            jsonString = str(json.dumps(callPayload))
            jsonDict = ast.literal_eval(jsonString)

            startTime = time.time()
            platform = function_call['platform']
            jsonResponse = ""

            # Make call depending on platform. Why does everyone's CLI have to be different?
            if (platform == 'HTTP' or platform == 'Azure'):
                response = requests.post(function_call['endpoint'], data=json.dumps(
                    callPayload), headers={'content-type': 'application/json'})
                jsonResponse = response.text
                print("Response: " + str(jsonResponse))
            elif (platform == 'AWS Lambda'):
                #client = boto3.client('lambda')
                #response = client.invoke(FunctionName = str(function_call['endpoint']), InvocationType='RequestResponse', Payload = jsonString.encode())
                #jsonResponse = response['Payload'].read().decode('ascii')
                #print("Response: " + str(jsonResponse))
                cmd = ['aws', 'lambda', 'invoke', '--invocation-type', 'RequestResponse', '--cli-read-timeout', '450', '--function-name', str(function_call['endpoint']), '--payload', jsonString, '/dev/stdout']
                proc = subprocess.Popen( cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                o, e = proc.communicate()
                print("STDOUT: " + str(o.decode('ascii')) + "\nSTDERR: " + str(e.decode('ascii')))
                jsonResponse = str(o.decode('ascii')).split('\n')[0][:-1]
            elif (platform == 'Google'):
                cmd = ['gcloud', 'functions', 'call', str(function_call['endpoint']), '--data', jsonString]
                proc = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                o, e = proc.communicate()
                print("STDOUT: " + str(o.decode('ascii')) + "\nSTDERR: " + str(e.decode('ascii')))
                jsonResponse = str(o.decode('ascii')).replace('\n', '')[34:-1]
            elif (platform == 'IBM'):
                cmd = ['ibmcloud', 'fn', 'action', 'invoke', '--result', str(function_call['endpoint'])]
                for key in jsonDict:
                    cmd.append('-p')
                    cmd.append(str(key))
                    cmd.append(str(jsonDict[key]))
                proc = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                o, e = proc.communicate()
                print("STDOUT: " + str(o.decode('ascii')) + "\nSTDERR: " + str(e.decode('ascii')))
                jsonResponse = str(o.decode('ascii'))

            timeSinceStart = round((time.time() - startTime) * 100000) / 100

            #
            # Get resonse object and add some information such as network latency, endpoint, and scrape csv-breaking characters from output.
            #
            try:
                dictionary = ast.literal_eval(jsonResponse)
                dictionary['2_thread_id'] = thread_id
                dictionary['1_run_id'] = i
                dictionary['zAll'] = "Final Results:"
                dictionary['roundTripTime'] = timeSinceStart
                dictionary['payload'] = str(callPayload)

                if 'runtime' in dictionary:
                    dictionary['latency'] = round(timeSinceStart - int(dictionary['runtime']), 2)

                if (len(function_calls)) > 1 and 'platform' not in dictionary:
                    dictionary['endpoint'] = function_call['endpoint']

                if 'version' in dictionary:
                    run_results.append(dictionary)

                key_list = list(dictionary.keys())
                for j in range(len(key_list)):
                    value = str(dictionary[key_list[j]])
                    dictionary[key_list[j]] = str(dictionary[key_list[j]]).replace(
                        ',', ';').replace('\t', '\\t').replace('\n', '\\n')

                print("Run " + str(thread_id) + "." + str(i) + " successful.")
            except Exception as e:
                print("Run " + str(thread_id) + "." +
                      str(i) + " failed: " + str(e))

    #
    # Create a bunch of threads and run make_call.
    #
    
    payloadList = payload
    while (len(payloadList) < total_runs):
        payloadList += payload
    random.shuffle(payloadList)
    payloadIndex = 0

    try:
        threadList = []
        for i in range(0, threads):
            for j in range(len(function_calls)):

                payloadsForThread = []
                while (len(payloadsForThread) < runs_per_thread):
                    payloadsForThread.append(payloadList[payloadIndex])
                    payloadIndex += 1

                thread = Thread(target=make_call, args=(i, runs_per_thread, function_calls[j], payloadsForThread))
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
