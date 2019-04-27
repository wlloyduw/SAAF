import json
import logging
from Inspector import *
import time

#
# Define your FaaS Function here.
# Each platform handler will call and pass parameters to this function.
# 
# @param request A JSON object provided by the platform handler.
# @returns A JSON object to use as a response.
#
def yourFunction(request):
    # Import the module and collect data
    inspector = Inspector()
    inspector.inspectAll()
    inspector.addTimeStamp("frameworkRuntime")

    # Add custom message and finish the function
    inspector.addAttribute("message", "Hello " + request['name'] + "!")
    return inspector.finish()