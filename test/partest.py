#!/usr/bin/python3

import time
import _thread as thread
import sys
import requests
import ast
import json

function = 'multiCalcService'
url = 'https://ydmsdru8hb.execute-api.us-east-1.amazonaws.com/default/multiCalcService'
payload = {'threads':2,'calcs':5000,'loops':100,'sleep':0}
headers = {'content-type':'application/json'}

#
# Start of the program.
#

threads = int(sys.argv[1])
runs_per_thread = int(int(sys.argv[2]) / threads)
runResults = []

# Define a function for the thread
def make_call( thread_id, runs):
	for i in range(0, runs):		
		response = requests.get(url, data=json.dumps(payload), headers=headers)
		dictionary = ast.literal_eval(response.text)
		dictionary['threadID'] = thread_id
		dictionary['run'] = i
		runResults.append(dictionary)
		print(dictionary)
		print("Request finished")

#
# Create a bunch of threads and run make_call.
#
try:
	threadList = []
	for i in range(0, threads):
		threadList.append(thread.start_new_thread(make_call, (i, runs_per_thread)))
except:
	print("Error: unable to start thread")
	
while(1):
	pass
	
	
print("All threads complete!")
