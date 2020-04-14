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
    'function': 'HELLOWORLD',
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
    'payloadFolder': '',
    'shufflePayloads': False,
    'runs': 10,
    'threads': 10,
    'iterations': 1,
    'sleepTime': 0,
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
    'warmupBuffer': 0,
    'experimentName': "DEFAULT-EXP",
    'passPayloads': False,
    'transitions': {}
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
if (len(sys.argv) > 1):

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
            overrides[overrideAttribute] = ""
        else:
            if mode == Mode.FUNC:
                functionList.append(arg)
            elif mode == Mode.EXP:
                expList.append(arg)
            elif mode == Mode.OUT:
                outDir = arg
            elif mode == Mode.OVERRIDE:
                overrides[overrideAttribute] += arg

    print("\nOverrides: " + str(overrides))

    #if (len(functionList) > 0 and len(expList) > 0 or True):
    if (not os.path.isdir(outDir)):
        os.mkdir(outDir)

    loadedFunctions = []
    loadedExperiments = []

    # Load in place the function files as dictionaries.
    for index, function in enumerate(functionList):
        nextFunction = json.load(open(function))
        nextFunction['sourceFile'] = function
        functionList[index] = nextFunction

    # Load in place the experiments files as dictionaries.
    for index, experiment in enumerate(expList):
        nextExperiment = json.load(open(experiment))
        nextExperiment['sourceFile'] = experiment
        nextExperiment['experimentName'] = os.path.basename(experiment).replace(".json", "")
        expList[index] = nextExperiment

    # Add in default function in the event none are supplied. If parameters have indices add more default functions.
    if (len(functionList) == 0):

        maxFunctions = 1
        for key in overrides:
            if '[' in key and ']' in key:
                subIndex = int(key[key.find('[')+1:key.find(']')]) + 1
                if subIndex > maxFunctions: maxFunctions = subIndex

        for i in range(0, maxFunctions):
            functionList.append(defaultFunction)

    # Add in default experiment in the event none are supplied. If parameters have indices add more default experiments.
    if (len(expList) == 0):
        maxExperiments = 1
        for key in overrides:
            if '[' in key and ']' in key:
                subIndex = int(key[key.find('[')+1:key.find(']')]) + 1
                if subIndex > maxExperiments: maxExperiments = subIndex

        for i in range(0, maxExperiments):
            expList.append(defaultExperiment)

    # Apply inheritance to function objects.
    for index, function in enumerate(functionList):
        # Set default options if needed.
        for key in defaultFunction:
            if key not in function:
                function[key] = defaultFunction[key]
                print("\nERROR: " + str(key) + " missing in function file! Using default option of " 
                    + str(defaultFunction[key]))

        # Add in overrides for function.
        for key in overrides:

            modifiedKey = key

            # If the key has an index skip it if index does not match function index.
            if '[' in key and ']' in key:
                subIndex = int(key[key.find('[')+1:key.find(']')])
                if index != subIndex: continue
                modifiedKey = key[:key.find('[')]

            function[modifiedKey] = overrides[key]

        print("\nLoaded function: " + str(function))
        loadedFunctions.append(function)

    # Load in experiment files
    for index, experiment in enumerate(expList):
        # Set default options if needed.
        for key in defaultExperiment:
            if key not in experiment:
                experiment[key] = defaultExperiment[key]
                print("\nERROR: " + str(key) + " missing in experiment file! Using default option of " 
                    + str(defaultExperiment[key]))

        # Add in overrides for experiments.
        for key in overrides:

            modifiedKey = key

            # If the key has an index skip it if index does not match experiment index.
            if '[' in key and ']' in key:
                subIndex = int(key[key.find('[')+1:key.find(']')])
                if index != subIndex: continue
                modifiedKey = key[:key.find('[')]

            value = overrides[key]
            try:
                # Try to load as an integer
                experiment[modifiedKey] = int(overrides[key])
            except ValueError:
                try:
                    # Try to load a JSON
                    experiment[modifiedKey] = json.loads(overrides[key])
                except ValueError as e:
                    # Give up and load a string
                    experiment[modifiedKey] = overrides[key]

        print("\nLoaded experiment: " + str(experiment))
        loadedExperiments.append(experiment)

    run_experiment(loadedFunctions, loadedExperiments, outDir)
else:
    print("Please supply parameteres! Usage:\n" +
    "./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: PATH FOR OUTPUT}")

