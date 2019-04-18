import thread
import time
import sys
import os
import subprocess
import shlex

function = 'multiCalcService'
json = '{\"threads\":2,\"calcs\":5000,\"loops\":100,\"sleep\":0}'

command = 'aws lambda invoke --invocation-type RequestResponse --function-name ' + function + ' --region us-east-1 --payload ' + json

# Define a function for the thread
def make_call( thread_id, runs):
	for i in range(0, runs):
		
		p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		 
		## Talk with date command i.e. read data from stdout and stderr. Store this info in tuple ##
		## Interact with process: Send data to stdin. Read data from stdout and stderr, until end-of-file is reached.  ##
		## Wait for process to terminate. The optional input argument should be a string to be sent to the child process, ##
		## or None, if no data should be sent to the child.
		(output, err) = p.communicate()
		 
		## Wait for date to terminate. Get return returncode ##
		p_status = p.wait()
		print "Command output : ", output
		print "Command exit status/return code : ", p_status

		print(p)

threads = int(sys.argv[1])
runs_per_thread = int(sys.argv[2]) / threads

# Create two threads as follows
try:
	for i in range(0, threads):
		thread.start_new_thread(make_call, (i, threads))
	
	#thread.start_new_thread( make_call, ("Thread-1", 2, ) )
	#thread.start_new_thread( make_call, ("Thread-2", 4, ) )
except:
	print "Error: unable to start thread"

while 1:
	pass
