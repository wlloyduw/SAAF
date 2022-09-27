import handler
import json

# Load json file into dict
config = {}
with open("config.json") as f:
	config = json.load(f)

print(json.dumps(handler.yourFunction(config["test_payload"], {})))
