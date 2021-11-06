import handler
import json

s3 = None

#
# AWS Lambda Functions Default Function
#
# This hander is used as a bridge to call the platform neutral
# version in handler.py. This script is put into the scr directory
# when using publish.sh.
#
# @param request
#
def lambda_handler(event, context):
	response = handler.yourFunction(event, context)
	
	# Async Implementation. If the request contains a bucket name
	# SAAF results will be saved to the bucket. Implemented so that
	# functions that are not async have minimal overhead (a single if statement and s3 variable assignment)
	if ('asyncBucket' in event):
		import boto3
		import uuid

		global s3
		if (s3 is None):
			s3 = boto3.resource('s3').Bucket(event['asyncBucket'])
		s3.Object('key').put(Body=json.dumps(response))
	return response
	