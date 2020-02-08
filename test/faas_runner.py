#!/usr/bin/env python3

#
# FaaS Runner is an interface to run FaaS experiments. Feed in function.json files and experiment.json files
# to determine how an experiment will execute and how the report will be generated.
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
from report_generator import report
from experiment_orchestrator import publish, run_experiment

# Default function options:
defaultFunction = {
    'function': 'helloWorld',
    'platform': 'AWS Lambda',
    'source': '../java_template',
    'endpoint': ''
}

# Default experiment options:
defaultExperiment = {
    'callWithCLI': True,
    'callAsync': False,
    'memorySettings': [],
    'parentPayload': {},
    'payloads': [{}],
    'shufflePayloads': False,
    'runs': 10,
    'threads': 10,
    'iterations': 1,
    'sleepTime': 1,
    'randomSeed': 42,
    'outputGroups': [],
    'outputRawOfGroup': [],
    'showAsList': [],
    'showAsSum': [],
    'ignoreFromAll': [],
    'ignoreFromGroups': [],
    'ignoreByGroup': [],
    'invalidators': {},
    'removeDuplicateContainers': False,
    'overlapFilter': "",
    'openCSV': True,
    'combineSheets': False,
    'warmupBuffer': 0
}

# Modes for parsing parameters.
class Mode(Enum):
    FUNC = 1
    EXP = 2
    OUT = 3
    NONE = 4
    OVERRIDE = 5

#
# Use command line arguments to select function and experiments.
#
if ("-f" not in sys.argv or "-e" not in sys.argv):
    print("Please supply parameteres! Usage:\n./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")
elif (len(sys.argv) > 1):

    mode = Mode.NONE

    outDir = "./history"
    overrides = {}

    functionList = []
    expList = []

    # Parse arguments
    for arg in sys.argv:
        if (arg == "-f"):
            mode = Mode.FUNC
        elif (arg == "-e"):
            mode = Mode.EXP
        elif (arg == "-o"):
            mode = Mode.OUT
        elif ('--' in arg):
            mode = Mode.OVERRIDE
            overrideAttribute = arg[2:]
            overrides.overrideAttribute = ""
        else:
            if mode == Mode.FUNC:
                functionList.append(arg)
            elif mode == Mode.EXP:
                expList.append(arg)
            elif mode == Mode.OUT:
                outDir = arg
            elif mode == Mode.OVERRIDE:
                overrides.overrideAttribute += arg

    if (len(functionList) > 0 and len(expList) > 0):
        if (not os.path.isdir(outDir)):
            os.mkdir(outDir)

        loadedFunctions = []
        loadedExperiments = []

        # Load in function files
        for function in functionList:
            nextFunction = json.load(open(function))
            nextFunction['sourceFile'] = function

            # Set default options if needed.
            for key in defaultFunction:
                if key not in nextFunction:
                    nextFunction[key] = defaultFunction[key]
                    print("ERROR: " + str(key) + " missing in function file! Using default option of " 
                        + str(defaultFunction[key]))

            loadedFunctions.append(nextFunction)

        # Load in experiment files
        for experiment in expList:
            nextExperiment = json.load(open(experiment))
            nextExperiment['sourceFile'] = experiment
            nextExperiment['experimentName'] = os.path.basename(experiment).replace(".json", "")

            # Set default options if needed.
            for key in defaultExperiment:
                if key not in nextExperiment:
                    nextExperiment[key] = defaultExperiment[key]
                    print("ERROR: " + str(key) + " missing in experiment file! Using default option of " 
                        + str(defaultExperiment[key]))
            loadedExperiments.append(nextExperiment)

        run_experiment(loadedFunctions, loadedExperiments, outDir)
    else:
        print("Please supply parameteres! Usage:\n./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")
else:
    print("Please supply parameteres! Usage:\n./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")

