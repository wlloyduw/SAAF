import functions_framework
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

@functions_framework.http
def hello_world(request):
    request_json = request.get_json()
    call = handler.yourFunction(request_json, None)
    return json.dumps(call)
