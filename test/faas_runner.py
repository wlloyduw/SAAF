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

    memoryList = exp['memorySettings']
    iterations = exp['iterations']
    sleepTime = exp['sleepTime']
    openCSV = exp['openCSV']
    combineSheets = exp['combineSheets']
    warmupBuffer = exp['warmupBuffer']

    if (not memoryList):
        memoryList.append(0)

    if (iterations <= 0):
        print("Invalid Parameters! Iterations must be >= 1!")
        return False

    if (combineSheets and (warmupBuffer > iterations or iterations == 1)):
        combineSheets = False
        print("Conflicting parameters. CombineSheets has been disabled...\nEither warmupBuffer > iterations or iterations == 1")

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
            runList.append(parTest([currentFunc], currentExp))

            if runList[i] != None:
                print("Test complete! Generating report...")
                partestResult = report(runList[i], currentExp, True)

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
                            # OS X
                            subprocess.call(["open", csvFilename])
                        elif sys.platform == "win32":
                            # Windows...
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
            partestResult = report(finalRunList, currentExp, False)
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
                    pass
                else:
                    print("Report generated. " + str(csvFilename) + " created.")
            except Exception:
                pass

    print("All tests complete!")



class FaaSRunner(cmd.Cmd):
    intro = "FaaS Runner: Type help or ? for help. Use < and > to switch FaaS Functions.\n"
    currentFunction = 0
    #prompt = "\n" + str(functions[currentFunction]) + ": "

    def do_clear(self, arg):
        'Clear the screen.'
        print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")

    def do_refresh(self, arg):
        'Destroy and republish a function.'

    #
    # Redeploy the function. Platforms like IBM and Google do not let you change memory values without completely redeploying the function.
    #
    def do_publish(self, arg):
        'Publish a function.'
        currentJson = "./functions/" + \
            str(functions[self.currentFunction]) + ".json"

        publish(currentJson)

    #
    # Open the configuration file of this function.
    #
    def do_edit(self, arg):
        'Edit the function configuration.'
        currentJson = "./functions/" + \
            str(functions[self.currentFunction]) + ".json"
        print("Opening " + currentJson)

        if sys.platform == "linux" or sys.platform == "linux2":
            # linux
            subprocess.call(["xdg-open", currentJson])
        elif sys.platform == "darwin":
            # OS X
            subprocess.call(["open", currentJson])
        elif sys.platform == "win32":
            # Windows...
            pass

    #
    # Open the folder containing the source code of this function.
    #
    def do_source(self, arg):
        'Open the source code of this function.'
        currentJson = "./functions/" + \
            str(functions[self.currentFunction]) + ".json"
        func = json.load(open(currentJson))
        print("Opening " + func['source'])

        if sys.platform == "linux" or sys.platform == "linux2":
            # linux
            subprocess.call(["xdg-open", func['source']])
        elif sys.platform == "darwin":
            # OS X
            subprocess.call(["open", func['source']])
        elif sys.platform == "win32":
            # Windows...
            pass

    def default(self, line):
        line = line.strip()
        if line == '>':
            self.currentFunction = (self.currentFunction + 1) % len(functions)
            self.prompt = "\n" + functions[self.currentFunction] + ": "
        elif line == '<':
            self.currentFunction = (self.currentFunction - 1) % len(functions)
            self.prompt = "\n" + functions[self.currentFunction] + ": "
        elif line[:3] == "run":
            line = line[4:]
            experiment = "./experiments/" + str(line) + ".json"

            currentJson = "./functions/" + \
                str(functions[self.currentFunction]) + ".json"

            run_experiment([currentJson], [experiment], "./history")

        else:
            pass

    def do_close(self, arg):
        'close the program.'
        return True


def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))

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
            #loadFunctions = True
            #loadExp = False
            #setOut = False
        elif (arg == "-e"):
            mode = Mode.EXP
            #loadFunctions = False
            #loadExp = True
            #setOut = False
        elif (arg == "-o"):
            mode = Mode.OUT
        else:
            if mode == Mode.FUNC:
                functionList.append(arg)
            elif mode == Mode.EXP:
                expList.append(arg)
            elif mode == Mode.OUT:
                outDir = arg
            #if loadFunctions:
            #    functionList.append(arg)
            #elif loadExp:
            #    expList.append(arg)

    run_experiment(functionList, expList, outDir)
else:
    #
    # Use FaaS Shell interface.
    #
    if __name__ == '__main__':
        print("Please supply parameteres! Usage:\n./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")
        #
        # Load functions.
        #
        #for filename in os.listdir("./functions"):
        #   if filename.endswith(".json"):
        #        functions.append(str(filename.replace(".json", "")))
        #
        #FaaSRunner().cmdloop()
