import json
import logging
from Inspector import *
import time

#
# Define your FaaS Function here.
# Each platform handler will call and pass parameters to this function.
# 
# @param request A JSON object provided by the platform handler.
# @param context A platform specific object used to communicate with the cloud platform.
# @returns A JSON object to use as a response.
#
def yourFunction(request, context):
    # Import the module and collect data
    inspector = Inspector()
    inspector.inspectAll()
    inspector.addTimeStamp("frameworkRuntime")

    # Add custom message and finish the function
    if ('name' in request):
        inspector.addAttribute("message", "Hello " + str(request['name']) + "!")
    else:
        inspector.addAttribute("message", "Hello World!")
    
    inspector.inspectCPUDelta()
    return inspector.finish()