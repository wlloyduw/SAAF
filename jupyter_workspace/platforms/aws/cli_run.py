from lambda_function import lambda_handler
import json
import os
import sys

event = json.loads(sys.argv[1])
print(lambda_handler(event, None))

