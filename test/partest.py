#!/usr/bin/python3

import time
import _thread as thread
import sys
import requests
import ast
import json
import datetime
from decimal import Decimal

url = 'https://2q0ng575ue.execute-api.us-east-1.amazonaws.com/calcservice_dev/'
payload = {'threads':2,'calcs':5000,'loops':100,'sleep':0}
headers = {'content-type':'application/json'}

#
# Start of the program.
#

threads = int(sys.argv[1])
total_runs = int(sys.argv[2])
runs_per_thread = int(total_runs / threads)
run_results = []

#
# Print starter information
#
print(datetime.datetime.now())
print("Setting up test: runsperthread=" + str(runs_per_thread) + " threads=" + str(threads) + " totalruns=" + str(total_runs))

# Define a function for the thread
def make_call( thread_id, runs):
	for i in range(0, runs):		
		response = requests.post(url, data=json.dumps(payload), headers=headers)
		dictionary = ast.literal_eval(response.text)
		dictionary['2_thread_id'] = thread_id
		dictionary['1_run_id'] = i
		if 'version' in dictionary:
			run_results.append(dictionary)
		
#
# Create a bunch of threads and run make_call.
#
try:
	threadList = []
	for i in range(0, threads):
		threadList.append(thread.start_new_thread(make_call, (i, runs_per_thread)))
except:
	print("Error: unable to start thread")
	
#
# Wait for threads to finish.
#
while(len(run_results) != total_runs):
	pass

#
# Print results of each run.
#
csv_header = ""
key_list = list(run_results[0].keys())
key_list.sort()
for i in range(len(key_list)):
	csv_header += key_list[i] + ","
csv_header = csv_header[:-1]
print("")
print("Raw results of each run:")
print(csv_header)

for i in range(len(run_results)):
	line = ""
	run = run_results[i]
	for i in range(len(key_list)):
		line += str(run[key_list[i]]) + ","
	line = line[:-1]
	print(line)

#
# Build new dictionaries for each category.
# key_map defines the dictionary to put runs with unique keys into.
#
key_map = {'uuid': {}, 'cpuType': {}, 'vmuptime': {}, 'newcontainer': {}, 'platform': {}, 'lang': {}, 'version': {}}
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
for i in range(len(master_key_list)):
	key_value = master_key_list[i]
	sub_key_list = list(key_map[key_value].keys())
	if len(sub_key_list) != 0:
		print("")
		print("Results for runs with attribute " + str(key_value) + ":")

		csv_header = str(key_value) + ",uses,"
		run_dict = key_map[key_value][sub_key_list[0]][0]
		run_attributes = list(run_dict.keys())
		run_attributes.sort()
		
		number_attributes = [];
		
		for i in range(len(run_attributes)):
			attribute = run_attributes[i];
			value = run_dict[attribute]
			try:
				Decimal(value)
				csv_header += "avg_" + str(attribute) + ","
				number_attributes.append(attribute)
			except:
				pass
		
		csv_header = csv_header[:-1]
		print(csv_header)
		
		for i in range(len(sub_key_list)):
			
			run_list = key_map[key_value][sub_key_list[i]]
			
			line = str(sub_key_list[i]) + "," + str(len(run_list)) + ","
			
			for j in range(len(number_attributes)):
				total_value = 0
				attribute = number_attributes[j]
				
				for k in range(len(run_list)):
					run_dict = run_list[k]
					total_value += Decimal(run_dict[attribute])
					
				line += str(round((total_value / len(run_list)), 2)) + ","
			
			line = line[:-1]
			print(line)
