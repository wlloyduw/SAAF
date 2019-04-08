import handler
import json

#
# Google Cloud Functions Default Function
#
# This hander is used as a bridge to call the platform neutral
# version in handler.py. This script is put into the scr directory
# when using publish.sh.
#
# @param request
#
def hello_world(request):
	"""Responds to any HTTP request.
	Args:
		request (flask.Request): HTTP request object.
	Returns:
		The response text or any set of values that can be turned into a
		Response object using
		`make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
	"""
	request_json = request.get_json()
	
	return json.dumps(handler.yourFunction(request_json))