#!/usr/bin/env python3

#
# FaaS Runner is an interface to run FaaS experiments. Feed in function.json files and experiment.json files
# to determine how partest will execute and how the report will be generated.
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

sys.path.append('./tools')
from partest import parTest
from report_generator import report

functions = []

def publish(function, memory):

    func = json.load(open(function))

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

    currentFunc = functions[0]
    currentExp = experiments[0]
    exp = json.load(open(currentExp))
    expName = os.path.basename(currentExp)
    expName = expName.replace(".json", "")
    func = json.load(open(currentFunc))


    functionName = func['function']
    platform = func['platform']

    threads = 100
    if ('threads' in exp):
        threads = exp['threads']

    runs = 100
    if ('runs' in exp):
        runs = exp['runs']

    if (threads > runs):
        print("Invalid Experiment! Error: Threads > Runs")
        return False

    memoryList = []
    if ('memorySettings' in exp):
        memoryList = exp['memorySettings']

    iterations = 1
    if ('iterations' in exp):
        iterations = exp['iterations']

    sleepTime = 0
    if ('sleepTime' in exp):
        sleepTime = exp['sleepTime']

    openCSV = True
    if ('openCSV' in exp):
        openCSV = exp['openCSV']

    combineSheets = False
    if ('combineSheets' in exp):
        combineSheets = exp['combineSheets']

    warmupBuffer = 0
    if ('warmupBuffer' in exp):
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
                publish(currentFunc, mem)
            elif platform == "IBM":
                publish(currentFunc, mem)
            else:
                print("Platform does not support changing memory values.")
        else:
            print("Skipping setting memory value.")

        print("Sleeping after setting memory value...")
        time.sleep(0)
        runList = []

        for i in range(iterations):
            print("Running test " + str(i) + ": ")
            runList.append(parTest([json.load(open(currentFunc))], json.load(open(currentExp))))

            if runList[i] != None:
                print("Test complete! Generating report...")
                partestResult = report(runList[i], json.load(open(currentExp)), True)

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
            time.sleep(0)

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
            partestResult = report(finalRunList, json.load(open(currentExp)), False)
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
#
# Modes for parsing parameters.
#
class Mode(Enum):
    FUNC = 1
    EXP = 2
    OUT = 3
    NONE = 4

#
# Use command line arguments to select function and experiements.
#
if ("-f" not in sys.argv or "-e" not in sys.argv):
    print("Please supply parameteres! Usage:\n./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")
elif (len(sys.argv) > 1):

    mode = Mode.NONE

    loadFunctions = False
    loadExp = False
    setOut = False
    outDir = "./history"

    functionList = []
    expList = []

    for arg in sys.argv:
        if (arg == "-f"):
            mode = Mode.FUNC
        elif (arg == "-e"):
            mode = Mode.EXP
        elif (arg == "-o"):
            mode = Mode.OUT
        else:
            if mode == Mode.FUNC:
                functionList.append(arg)
            elif mode == Mode.EXP:
                expList.append(arg)
            elif mode == Mode.OUT:
                outDir = arg

    if (len(functionList) > 0 and len(expList) > 0):
        if (not os.path.isdir(outDir)):
            os.mkdir(outDir)

        run_experiment(functionList, expList, outDir)
    else:
        print("Please supply parameteres! Usage:\n./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")
else:
    print("Please supply parameteres! Usage:\n./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")

