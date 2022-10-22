import handler
import json
import sys

request = json.loads(sys.argv[1])

print(json.dumps(handler.yourFunction(request, {})))
