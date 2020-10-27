#!/usr/bin/env python3

#
# @author Robert Cordingly
#
import ast
import cmd
import datetime
import json
import os
import subprocess
import sys
import time
from decimal import Decimal
from enum import Enum

from experiment_caller import callExperiment
from experiment_caller import callPipelineExperiment
from report_generator import report
from report_generator import write_file

#
# Some platforms require you to redeploy you code to change
# memory settings. This method uses a functions 'source' attribute
# to locate the publish.sh script and redeploy your function with
# a different memory setting.
#
def publish(func, memory):
    sourceDir = func['source']
    deployConfig = sourceDir + "/deploy/config.json"
    deployJson = json.load(open(deployConfig))

    if (deployJson['functionName'] != func['function']):
        print("Error! Deployment configuration does not match the current function. Please correct deployment files.")
        if sys.platform == "linux" or sys.platform == "linux2":
            # linux
            subprocess.call(["xdg-open", function])
            subprocess.call(["xdg-open", deployConfig])
        elif sys.platform == "darwin":
            # OS X
            subprocess.call(["open", function])
            subprocess.call(["open", deployConfig])
        elif sys.platform == "win32":
            # Windows...
            pass
    else:
        platform = func['platform']

        if (memory == None): 
            memory = 512

        params = []
        if platform == "AWS Lambda":
            params = ['1', '0', '0', '0', str(memory)]
        elif platform == "Google":
            params = ['0', '1', '0', '0', str(memory)]
        elif platform == "IBM":
            params = ['0', '0', '1', '0', str(memory)]
        elif platform == "Azure":
            params = ['0', '0', '0', '1', str(memory)]
        else:
            print("Unknown platform.")
            return None

        cmd = [sourceDir + "/deploy/publish.sh"] + params
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()

        print(str(o))

#
# For each experiment, merge each payload with 
# the parent payload.
#
# Load payloads from a folder if needed. Payloads will be
# merged based off of this priority:
# payloads > payloadfolder > parent
#
# If there are more payloads loaded from a folder than payloads in the list,
# payloads in the list will be duplicated to match the size of the payload folder.
#
def prepare_payloads(experiments):
    print("\n-----------------------------------------------------------------")
    print("PREPARING PAYLOADS... (experiment_orchestrator.py)")
    print("-----------------------------------------------------------------\n")


    for i, exp in enumerate(experiments):

        # Load payloads from folder.
        payloadFolder = exp['payloadFolder']
        payloadsFromFolder = []
        if (payloadFolder != "" and os.path.isdir(payloadFolder)):
            for filename in os.listdir(payloadsFromFolder):
                if filename.endswith(".json"):
                    try:
                        payloadsFromFolder.append(json.load(open(payloadsFromFolder + '/' + str(filename))))
                    except Exception as e:
                        print("Error loading: " + payloadsFromFolder + '/' + str(filename) + " with exception " + str(e))
                        pass
            
            # Duplicate payloads to have same number as payloads folder. Trim some off if there is more.
            while len(exp['payloads'] < len(payloadsFromFolder)):
                exp['payloads'] += exp['payloads']
            exp['payloads'] = exp['payloads'][:len(payloadsFromFolder)]

            # Create new 'payloads' list based off loaded payloads.
            newPayloadList = []
            for j, payload in enumerate(exp['payloads']):
                otherPayload = payloadsFromFolder[j]
                newPayloadList.append({**otherPayload, **payload})
            experiments[i]['payloads'] = newPayloadList
        else:
            print("Not loading payloads from folder. Either folder does not exist of payloadFolder is undefined.")

        # Update payload list based off of parent payload.
        parentPayload = exp['parentPayload']
        for j, payload in enumerate(exp['payloads']):
            newPayload = {**parentPayload, **payload}
            experiments[i]['payloads'][j] = newPayload

    return experiments

#
# This method andles executing the experiment with exeperiment_caller,
# automatically changes memory values, calls the report_generator and
# writes the output to disk.
#
def run_experiment(functions, experiments, outDir):

    experiments = prepare_payloads(experiments)

    exp = experiments[0]
    expName = exp['experimentName']
    func = functions[0]
    functionName = func['function']
    platform = func['platform']
    threads = exp['threads']
    runs = exp['runs']

    if (threads > runs):
        print("Invalid Experiment! Error: Threads > Runs")
        return False

    memoryList = exp['memorySettings']
    iterations = exp['iterations']
    sleepTime = exp['sleepTime']
    openCSV = exp['openCSV']
    combineSheets = exp['combineSheets']
    warmupBuffer = exp['warmupBuffer']

    if (not memoryList):
        memoryList.append(0)

    if (iterations <= 0):
        print("Invalid Experiment! Iterations must be >= 1!")
        return False

    if (combineSheets and (warmupBuffer > iterations or iterations == 1)):
        combineSheets = False
        print("Conflicting experiment parameters. CombineSheets has been disabled...\nEither warmupBuffer > iterations or iterations == 1")

    for mem in memoryList:
        if mem != 0:
            # Update memory value based on platform, hopefully without redeploying function.
            print("Setting memory value to: " + str(mem) + "MBs...")

            if platform == "AWS Lambda":
                cmd = ['aws', 'lambda', 'update-function-configuration',
                    '--function-name', functionName, '--memory-size', str(mem)]
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                o, e = proc.communicate()
                print(str(o.decode('ascii')))
            elif platform == "Google":
                publish(func, mem)
            elif platform == "IBM":
                publish(func, mem)
            else:
                print("Platform does not support changing memory values.")
        else:
            print("Skipping setting memory value.")

        print("Sleeping after setting memory value...")
        time.sleep(sleepTime)
        runList = []

        for i in range(iterations):
            print("Running test " + str(i) + ": ")

            if (len(experiments) > 1 and len(functions) > 1 and len(experiments) == len(functions)):
                print("Running in pipeline mode... " + str(functions))
                runList.append(callPipelineExperiment(functions, experiments))
            else:
                runList.append(callExperiment([func], exp))

            if runList[i] != None:
                print("Test complete! Generating report...")
                partestResult = report(runList[i], exp)

                print(partestResult)

                baseFileName = outDir + "/" + functionName + "-" + str(
                        expName) + "-" + str(mem) + "MBs-run" + str(i)
                write_file(baseFileName, partestResult, openCSV, runList[i])

            print("Sleeping before next test...")
            time.sleep(sleepTime)

        if (combineSheets):
            print("Generating Combined Report:")
            finalRunList = []
            for i in range(iterations):
                if (i > warmupBuffer - 1):
                    for run in runList[i]:
                        run['iteration'] = i
                        if 'vmID' in run:
                            run['vmID[iteration]'] = run['vmID'] + "[" + str(i) + "]"
                    finalRunList.extend(runList[i])
            print(str(finalRunList))
            partestResult = report(finalRunList, exp)

            baseFileName = outDir + "/" + functionName + "-" + str(
                    expName) + "-" + str(mem) + "MBs-COMBINED"
            write_file(baseFileName, partestResult, True)



    print("All tests complete!")
