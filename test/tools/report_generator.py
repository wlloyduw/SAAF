#!/usr/bin/env python3

import ast
import datetime
import json
import os
import random
import subprocess
import sys
import time
import uuid
from decimal import Decimal

#
# Parse a list of FaaS Response objects into a report.
#
# Reports can be broken into groups.
#
# @author Robert Cordingly
#
def report(responses, exp):
    print("\n-----------------------------------------------------------------")    
    print("GENERATING REPORT... (report_generator.py)")
    print("-----------------------------------------------------------------\n")


    output = ""
    threads = exp['threads']
    total_runs = exp['runs']
    runs_per_thread = int(total_runs / threads)

    payload = exp['payloads']

    # After runs all are finished, runs will be divided into categories based on this list.
    categories = exp['outputGroups']

    list_runs_of_category = exp['outputRawOfGroup']

    # In the category breakdown, these values will be displayed as a list of unqiue values instead of an average or being ignored.
    list_category = exp['showAsList']

    # In the category breakdown, these values will be added up rather an showing an average or list.
    sum_category = exp['showAsSum']

    # These attributes will be excluded from the raw run results and category breakdown. If one of these is listed as a category, runs will still be categorized by this attribute.
    ignore_attributes = exp['ignoreFromAll']

    # These attributes will not be excluded from the raw run results but will be excluded from the category breakdown.
    ignore_attributes_from_all_categories = exp['ignoreFromGroups']

    # These attributes will not be excluded from the raw run results but will be excluded from a specific category in the category breakdown.
    ignore_attributes_from_specific_categories = exp['ignoreByGroup']

    # Runs with these attributes and values will be removed from the category breakdown. All runs will still be shown in the raw output.
    invalidators = exp['invalidators']

    # If a container is reused during one experiment (non-concurrent calls) they will be removed from the report.
    removeDuplicateContainers = exp['removeDuplicateContainers']

    overlapFilter = exp['overlapFilter']

    for dictionary in responses:
        if 'vmID' in dictionary and 'vmuptime' in categories:
            categories.remove('vmuptime')
            if 'vmuptime' in list_category:
                list_category.remove('vmuptime')

        if 'containerID' in dictionary and 'uuid' in categories:
            categories.remove('uuid')
            if 'uuid' in list_category:
                list_category.remove('uuid')

    run_results = responses

    #
    # Fill in missing keys.
    #
    runKeyList = []
    for run in run_results:
        for key in list(run.keys()):
            if key not in runKeyList:
                runKeyList.append(key)
    for run in run_results:
        for key in runKeyList:
            if key not in run:
                print("PAYLOADS DO NOT CONTAIN EQUIVALENT ATTRIBUTES. MISSING ATTRIBUTES WILL BE FILLED WITH -999999999999 PURPOSEFULLY MAKING SUMS AND AVERAGES INCORRECT AS THEY CAN NO LONGER BE CALCULATED PROPERLY.")
                run[key] = -999999999999

    #
    # Insert runtimeOverlap into runs.  
    #
    if 'startTime' in run_results[0] and 'endTime' in run_results[0]:
        for i in range(len(run_results)):
            run1 = run_results[i]
            start1 = int(run1['startTime'])
            end1 = int(run1['endTime'])
            length1 = max(end1 - start1, 1)
            totalDist = 0
            for j in range(len(run_results)):
                if i == j: continue
                run2 = run_results[j]
                if (overlapFilter != "" and overlapFilter != None):
                    if (overlapFilter in run1 and overlapFilter in run2):
                        if (run1[overlapFilter] != run2[overlapFilter]):
                            continue
                    else:
                        continue
                start2 = max(min(int(run2['startTime']), end1), start1)
                end2 = max(min(int(run2['endTime']), end1), start1)
                length2 = end2 - start2
                totalDist += length2 / length1
            run1['runtimeOverlap'] = str(round(totalDist, 2))

    # Calculate pipline metrics.
    if '3_pipeline_stage' in run_results[0]:
        # Create 3D grid datastructure where x = run_id, y = thread_id, and z = 3_pipeline_stage
        maxX = 0
        maxY = 0
        maxZ = 0

        # Find the max values of each dimmension
        for i in range(len(run_results)):
            run = run_results[i]
            x = int(run['1_run_id'])
            y = int(run['2_thread_id'])
            z = int(run['3_pipeline_stage'])
            if (x > maxX): maxX = x
            if (y > maxY): maxY = y
            if (z > maxZ): maxZ = z

        # Create 3D lists of size
        pipelineList = [[[None for col in range(maxZ + 1)] for col in range(maxY + 1)] for row in range(maxX + 1)]

        # Distribute runs into data structure.
        for i in range(len(run_results)):
            run = run_results[i]
            x = int(run['1_run_id'])
            y = int(run['2_thread_id'])
            z = int(run['3_pipeline_stage'])
            run['index'] = i
            pipelineList[x][y][z] = run

        # Sort Z by pipeline stage.
        for x in pipelineList:
            for y in x:
                y = sorted(y, key=lambda k: k['3_pipeline_stage'])
                previous = None
                for z in y:
                    print(str(z['1_run_id'])+"-"+str(z['2_thread_id']) +"-"+str(z['3_pipeline_stage']))
                    temp = dict(z)
                    for key in z:
                        try:
                            value = round(float(temp[key]), 2)
                            if previous != None and key+"Pipeline" in previous:
                                temp[key + "Pipeline"] = value + previous[key + "Pipeline"]
                            else:
                                temp[key + "Pipeline"] = value
                        except:
                            pass

                    z = dict(temp)
                    run_results[z['index']] = dict(z)
                    print(str(z))
                    previous = z


        

    #
    # Print starter information
    #
    output += str(datetime.datetime.now()) + " - Python Partest Version 0.5\n"
    output += "Setting up test: runsperthread=" + str(runs_per_thread) + " threads=" + str(
        threads) + " totalruns=" + str(total_runs) + " payload=" + str(payload).replace(",","") + "\n"

    csv_header = ""
    key_list = list(run_results[0].keys())
    key_list.sort()
    for i in range(len(key_list)):
        if key_list[i] not in ignore_attributes:
            csv_header += key_list[i] + ","
    csv_header = csv_header[:-1]
    output += "\n"
    output += "Raw results of each run:\n"
    output += csv_header + "\n"

    for i in range(len(run_results)):
        line = ""
        run = run_results[i]
        for i in range(len(key_list)):
            if key_list[i] not in ignore_attributes:
                if key_list[i] in run:
                    line += str(run[key_list[i]]) + ","
                else:
                    line += "NONE,"
        line = line[:-1]
        output += line + "\n"
    output += "Successful Runs: " + str(len(run_results)) + "\n"

    #
    # Purge runs list of runs with specific invalid parameters or duplicate containers.
    #
    invalidRuns = []
    invalidKeys = list(invalidators.keys())
    containers = []
    for i in range(len(run_results)):
        run = run_results[i]

        if removeDuplicateContainers:
            if run['uuid'] in containers:
                invalidRuns.append(run)
            else:
                containers.append(run['uuid'])

        for j in range(len(invalidKeys)):
            key_value = invalidKeys[j]
            if key_value in list(run.keys()) and str(run[key_value]) == str(invalidators[key_value]):
                invalidRuns.append(run)

    if len(invalidRuns) > 0:
        output += "\n" + str(len(invalidRuns)) + \
            " runs removed from categories....\n"
        for i in range(len(invalidRuns)):
            if invalidRuns[i] in run_results:
                run_results.remove(invalidRuns[i])

    #
    # Insert zTenancy attribute as a combination of CPU Type and VM uses.
    #
    valid = True
    if 'zTenancy[vmID[iteration]]' in categories or 'zTenancy[vmID]' in categories:
        tenancyAttributes = ['vmID', 'vmID[iteration]']
        for attribute in tenancyAttributes:
            vm_dictionary = {}
            for i in range(len(run_results)):
                run = run_results[i]
                if attribute not in run:
                    valid = False
                    break

                if run[attribute] in vm_dictionary:
                    vm_dictionary[run[attribute]]['uses'] += 1
                else:
                    vm_dictionary[run[attribute]] = {
                        'uses': 1, 'cpuType': run['cpuType']}
            if valid:
                for i in range(len(run_results)):
                    run = run_results[i]
                    run['zTenancy[' + attribute + ']'] = str(vm_dictionary[run[attribute]]['cpuType']) + \
                        " - " + str(vm_dictionary[run[attribute]]['uses'])
                    run['tenants[' + attribute + ']'] = vm_dictionary[run[attribute]]['uses']
                    if attribute == 'vmID[iteration]' and 'zTenancy[vmID]' in categories:
                        # If multiple iterations are used, this tenancy value is NOT correct as calls over different iterations will
                        # count toward the tenancy count when they should not! zTenancy[vmID[iteration]] should be used.
                        categories.remove('zTenancy[vmID]')

    #
    # Build new dictionaries for each category.
    # key_map defines the dictionary to put runs with unique keys into.
    #
    key_map = {}
    for i in range(len(categories)):
        key_map[categories[i]] = {}

    master_key_list = list(key_map.keys())
    for i in range(len(run_results)):
        run = run_results[i]
        for i in range(len(master_key_list)):
            target_key = master_key_list[i]
            if target_key in list(run.keys()):
                if run[target_key] not in list(key_map[target_key].keys()):
                    key_map[target_key][run[target_key]] = [run]
                else:
                    key_map[target_key][run[target_key]].append(run)

    #
    # Loop through every dictionary created previously.
    # Find values that can be parsed into doubles and calculate the average of them.
    #
    master_key_list.sort()
    for i in range(len(master_key_list)):
        key_value = master_key_list[i]
        sub_key_list = list(key_map[key_value].keys())
        if len(sub_key_list) != 0:
            output += "\n"
            output += "Category " + \
                str(key_value) + ":\n"

            csv_header = str(key_value) + ",uses,"
            run_dict = key_map[key_value][sub_key_list[0]][0]
            run_attributes = list(run_dict.keys())
            run_attributes.sort()
            number_attributes = []

            # Build CSV Header Line
            for i in range(len(run_attributes)):
                attribute = run_attributes[i]

                valid = True
                if attribute in ignore_attributes or attribute in ignore_attributes_from_all_categories:
                    valid = False

                if key_value in ignore_attributes_from_specific_categories:
                    if attribute in list(ignore_attributes_from_specific_categories[key_value]):
                        valid = False

                if valid:
                    if attribute in list_category:
                        csv_header += str(attribute) + "_list,"
                        number_attributes.append(attribute)
                    elif attribute in sum_category:
                        try:
                            value = run_dict[attribute]
                            Decimal(value)
                            csv_header += "sum_" + str(attribute) + ","
                            number_attributes.append(attribute)
                        except:
                            pass
                    else:
                        try:
                            value = run_dict[attribute]
                            Decimal(value)
                            csv_header += "avg_" + str(attribute) + ","
                            number_attributes.append(attribute)
                        except:
                            pass

            csv_header = csv_header[:-1]
            output += csv_header + "\n"

            # Print out each run of this category.
            try:
                sub_key_list.sort()
            except Exception as e:
                print(str(e))
            for i in range(len(sub_key_list)):
                run_list = key_map[key_value][sub_key_list[i]]
                uses_of_category = len(run_list)
                line = str(sub_key_list[i]) + "," + str(uses_of_category) + ","
                for j in range(len(number_attributes)):
                    attribute = number_attributes[j]

                    valid = True
                    if attribute in ignore_attributes or attribute in ignore_attributes_from_all_categories:
                        valid = False

                    if key_value in ignore_attributes_from_specific_categories:
                        if attribute in list(ignore_attributes_from_specific_categories[key_value]):
                            valid = False

                    if valid:
                        if attribute in list_category:
                            attribute_list = []
                            for k in range(len(run_list)):
                                run_dict = run_list[k]
                                if run_dict[attribute] not in attribute_list:
                                    attribute_list.append(run_dict[attribute])
                            try:
                                attribute_list.sort()
                            except Exception as e:
                                print("Could not perform sort... " + str(e))
                            line += str(attribute_list).replace(',', ';') + ","
                        elif attribute in sum_category:
                            total_value = 0
                            for k in range(len(run_list)):
                                run_dict = run_list[k]
                                try:
                                    total_value += Decimal(run_dict[attribute])
                                except Exception as e:
                                    print("Could not perform math... " + str(e))
                            line += str(total_value) + ","
                        else:
                            total_value = 0
                            for k in range(len(run_list)):
                                run_dict = run_list[k]
                                try:
                                    total_value += Decimal(run_dict[attribute])
                                except Exception as e:
                                    print("Could not perform math..." + str(e))
                            line += str(round((total_value /
                                               len(run_list)), 2)) + ","
                line = line[:-1]
                output += line + "\n"				
            output += "Total number of unique " + str(key_value) + "s: " + str(len(sub_key_list)) + "\n"

            # Print out raw results of category.
            if key_value in list_runs_of_category:

                output += "\n--- Runs of Group " + str(key_value) + " ---\n"

                for i in range(len(sub_key_list)):
                    run_list = key_map[key_value][sub_key_list[i]]
                    output += "\nCategory " + str(key_value) + " with " + str(sub_key_list[i]) + ":\n"
                    
                    run_attributes = list(run_list[0].keys())
                    run_attributes.sort()

                    # Build CSV Header Line
                    csv_header = ""
                    for i in range(len(run_attributes)):
                        attribute = run_attributes[i]

                        valid = True
                        if attribute in ignore_attributes or attribute in ignore_attributes_from_all_categories:
                            valid = False

                        if key_value in ignore_attributes_from_specific_categories:
                            if attribute in list(ignore_attributes_from_specific_categories[key_value]):
                                valid = False

                        if valid:
                            csv_header += str(attribute) + ","
                    csv_header = csv_header[:-1]
                    output += csv_header + "\n"

                    for run in run_list:
                        line = ""
                        for attribute in run_attributes:
                            valid = True
                            if attribute in ignore_attributes or attribute in ignore_attributes_from_all_categories:
                                valid = False

                            if key_value in ignore_attributes_from_specific_categories:
                                if attribute in list(ignore_attributes_from_specific_categories[key_value]):
                                    valid = False

                            if valid:
                                line += str(run[attribute]) + ","
                        line = line[:-1]
                        output += line + "\n"
    return output

#
# Generate a report based off of a folder of payloads.
#
def report_from_folder(path, exp):
    print("\n-----------------------------------------------------------------")    
    print("GENERATING REPORT FROM FOLDER... (report_generator.py)")
    print("-----------------------------------------------------------------\n")


    if (not os.path.isdir(path)):
        print("Directory does not exist!")
        return ""

    run_list = []
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            try:
                run = json.load(open(path + '/' + str(filename)))
                run_list.append(run)
            except Exception as e:
                print("Error loading: " + path + '/' + str(filename) + " with exception " + str(e))
                pass
        else:
            continue

    print(str(run_list))
    return report(run_list, exp)

#
# Write the output file of a report, print a folder of runs if needed.
#
def write_file(baseFileName, data, openFile, runList = []):
    print("\n-----------------------------------------------------------------")    
    print("WRITING REPORT TO FILE... (report_generator.py)")
    print("-----------------------------------------------------------------\n")

    try:
        if (os.path.isfile(baseFileName + ".csv")):
            duplicates = 1
            while (os.path.isfile(baseFileName + "-" + str(duplicates) + ".csv")):
                duplicates += 1
            baseFileName += "-" + str(duplicates)

        # Write runs to folder if needed.
        if (len(runList) > 0):
            print("Writing raw runs to folder " + baseFileName)
            if not os.path.exists(baseFileName):
                os.makedirs(baseFileName)
                for i, run in enumerate(runList):
                    temp = uuid.uuid4()
                    file = open(baseFileName + '/run' + str(i) + '-' + str(temp) + '.json', 'w') 
                    file.write(json.dumps(run)) 
                    file.close() 

        baseFileName += ".csv"
        text = open(baseFileName, "w")
        text.write(str(data))
        text.close()

        if (openFile):
            print("Opening results...")
            if sys.platform == "linux" or sys.platform == "linux2":
                # linux
                subprocess.call(["xdg-open", baseFileName])
            elif sys.platform == "darwin":
                # MacOS
                subprocess.call(["open", baseFileName])
            elif sys.platform == "win32":
                # Windows...
                print("File created: " + str(baseFileName))
                pass
            else:
                print("Partest complete. " + str(baseFileName) + " created.")
    except Exception as e:
        print("Exception occurred: " + str(e))
        pass