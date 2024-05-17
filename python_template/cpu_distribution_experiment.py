import FaaSET
import FaaSRunner
import json


import os
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES' # MACOS MUST SET ENVIRONMENT VARIABLE TO AVOID FORK SAFETY ISSUE

regions = {
    "af-south-1": {"lat": -34.0486, "lon": 18.4811},
    "ap-east-1": {"lat": 22.285521, "lon": 114.157692},
    "ap-northeast-1": {"lat": 35.6893, "lon": 139.6899},
    "ap-northeast-2": {"lat": 37.4585, "lon": 126.7015},
    "ap-northeast-3": {"lat": 34.6946, "lon": 135.5021},
    "ap-south-1": {"lat": 19.0748, "lon": 72.8856},
    "ap-southeast-1": {"lat": 1.3036, "lon": 103.8554},
    "ap-southeast-2": {"lat": -33.8715, "lon": 151.2006},
    "ca-central-1": {"lat": 45.4995, "lon": -73.5848},
    "eu-central-1": {"lat": 50.1188, "lon": 8.6843},
    "eu-north-1": {"lat": 59.3287, "lon": 18.0717},
    "eu-south-1": {"lat": 45.4722, "lon": 9.1922},
    "eu-west-1": {"lat": 53.3379, "lon": -6.2591},
    "eu-west-2": {"lat": 51.5164, "lon": -0.093},
    "eu-west-3": {"lat": 48.8323, "lon": 2.4075},
    "sa-east-1": {"lat": -23.5335, "lon": -46.6359},
    "us-east-1": {"lat": 39.0469, "lon": -77.4903},
    "us-east-2": {"lat": 39.9625, "lon": -83.0061},
    "us-west-1": {"lat": 37.1835, "lon": -121.7714},
    "us-west-2": {"lat": 45.8234, "lon": -119.7257},
    "ca-west-1": {"lat": 53.7267, "lon": -127.6476},
    "ap-south-2": {"lat": 19.9975, "lon": 73.7898},
    "ap-southeast-3": {"lat": 1.3521, "lon": 103.8198},
    "ap-southeast-4": {"lat": 1.3521, "lon": 103.8198},
    "eu-south-2": {"lat": 41.9028, "lon": 12.4964},
    "eu-central-2": {"lat": 50.1109, "lon": 8.6821},
    "me-south-1": {"lat": 24.7743, "lon": 46.7384},
    "me-central-1": {"lat": 24.7743, "lon": 46.7384},
    "il-central-1": {"lat": 31.0461, "lon": 34.8516}
}

# Load sky_mesh.json into function_urls dictionary
function_urls = json.load(open("sky_mesh.json"))

def hello_world(request, inspector):
    inspector.addAttribute("message", "Hello, World!")
    return None

payload = FaaSET.dynamic_get_payload(hello_world, {})

import time

for region in regions.keys():
    try:
        name = "skyf_2048_" + region
        function_url = function_urls[name]
        data = FaaSRunner.fast_experiment(function_url, processes=100, runs_per_process=1, payloads=[payload], experiment_name=name)
        # Write data to a csv file it is a dataframe from pandas
        data.to_csv("./" + name + ".csv")
        print("Finished " + name + " experiment.")
        time.sleep(10)
    except Exception as e:
        print(str(e))
        pass