
import handler
import json
import sys
import os

#
# IBM Cloud Functions Default Function
#
# This hander is used as a bridge to call the platform neutral
# version in handler.py. This script is put into the scr directory
# when using publish.sh.
#
# @param request
#
def main(dict):
    return {"Wow": "Cool"}
	#return handler.yourFunction(dict, None)