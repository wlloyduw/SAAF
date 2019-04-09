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
	request_json = request.get_json()
	return json.dumps(handler.yourFunction(request_json))