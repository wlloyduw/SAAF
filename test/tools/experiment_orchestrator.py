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
from report_generator import report

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

def run_experiment(functions, experiments, outDir):

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
            runList.append(callExperiment([func], exp))

            if runList[i] != None:
                print("Test complete! Generating report...")
                partestResult = report(runList[i], exp, True)

                try:
                    csvFilename = outDir + "/" + functionName + "-" + str(
                        expName) + "-" + str(mem) + "MBs-run" + str(i)
                    if (os.path.isfile(csvFilename + ".csv")):
                        duplicates = 1
                        while (os.path.isfile(csvFilename + "-" + str(duplicates) + ".csv")):
                            duplicates += 1
                        csvFilename += "-" + str(duplicates)
                    csvFilename += ".csv"
                    text = open(csvFilename, "w")
                    text.write(str(partestResult))
                    text.close()

                    if openCSV:
                        print("Partest complete. Opening results...")
                        if sys.platform == "linux" or sys.platform == "linux2":
                            # linux
                            subprocess.call(["xdg-open", csvFilename])
                        elif sys.platform == "darwin":
                            # MacOS
                            subprocess.call(["open", csvFilename])
                        elif sys.platform == "win32":
                            # Windows...
                            print("File created: " + str(csvFilename))
                            pass
                    else:
                        print("Partest complete. " + str(csvFilename) + " created.")
                except Exception:
                    pass

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
            partestResult = report(finalRunList, exp, False)
            try:
                csvFilename = outDir + "/" + functionName + "-" + str(
                    expName) + "-" + str(mem) + "MBs-COMBINED"
                if (os.path.isfile(csvFilename + ".csv")):
                    duplicates = 1
                    while (os.path.isfile(csvFilename + "-" + str(duplicates) + ".csv")):
                        duplicates += 1
                    csvFilename += "-" + str(duplicates)
                csvFilename += ".csv"
                text = open(csvFilename, "w")
                text.write(str(partestResult))
                text.close()
                if sys.platform == "linux" or sys.platform == "linux2":
                    # linux
                    subprocess.call(["xdg-open", csvFilename])
                elif sys.platform == "darwin":
                    # OS X
                    subprocess.call(["open", csvFilename])
                elif sys.platform == "win32":
                    # Windows...
                    print("File created: " + str(csvFilename))
                    pass
                else:
                    print("Report generated. " + str(csvFilename) + " created.")
            except Exception:
                pass

    print("All tests complete!")
