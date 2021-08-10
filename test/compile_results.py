#!/usr/bin/env python3

import time
import os
import sys
import json
import shutil
import subprocess
from threading import Thread

sys.path.append('./tools')
from report_generator import report_from_folder
from report_generator import write_file

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
    'transitions': {},
    'simpleOutput': True
}

#Input parameteres
folderName = ''
experimentfile = './experiments/exampleExperiment.json'
delete = False
if (len(sys.argv) != 3):
    print("Please supply parameteres! Usage:\n./compile_results.py {FOLDER PATH} {PATH TO EXPERIMENT JSON}")
elif (len(sys.argv) == 3):
    folderName = sys.argv[1]
    experimentfile = sys.argv[2]

    # Create report text and save to csv file.
    print("Generating Report...")
    expName = os.path.basename(experimentfile)
    expName = expName.replace(".json", "")
    
    experiment = json.load(open(experimentfile))
    
    for key in defaultExperiment:
        if key not in experiment:
            experiment[key] = defaultExperiment[key]
    
    partestResult = report_from_folder(folderName, experiment)

    baseFileName = folderName + "/" + "compiled-results-" + str(expName)

    write_file(baseFileName, partestResult, True)