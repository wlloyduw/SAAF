#!/usr/bin/env python3

#
# Write the FaaS Runner function and experiment files for every workload in payloads.json.
#
#   functions/<deployment>/<workload>.json   One per deployment in workloads/config.json. Every
#                                            deployment is called over HTTP: the Web Function's
#                                            endpoint, the event function's function URL, or a
#                                            MicroVM's endpoint, which microvm.sh fills in.
#   experiments/<workload>/<experiment>.json  The same payload from payloads.json in each.
#
# Endpoints come from endpoints.json, which endpoints.sh fills in from AWS. A deployment without an
# endpoint gets an empty one, and run.sh skips it.
#
#   python3 generate.py
#
import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
workloads = here.parents[1] / "workloads"

# Each burst's size and how many times it repeats. Some repeat fewer times, to keep the cost down.
BURSTS = [(10, 10), (20, 10), (50, 5), (100, 5), (200, 3), (500, 2), (1000, 1)]

# Name, runs, threads, and iterations. Each burst sends threads requests at once, iterations times.
EXPERIMENTS = [("sequential-0100", 100, 1, 1)] + [("burst-%04d" % n, n, n, i) for n, i in BURSTS]

# A few sequential requests, to check a payload's runtime before running the experiments.
PILOT = ("pilot", 3, 1, 1)

# Every setting FaaS Runner reads, so it does not fill in defaults such as opening each CSV.
SETTINGS = {
    "callWithCLI": False,
    "callAsync": False,
    "memorySettings": [],
    "parentPayload": {},
    "payloadFolder": "",
    "shufflePayloads": False,
    "sleepTime": 10,
    # A request with no response after 60 seconds fails, and the experiment stops after that burst.
    "timeout": 60,
    "randomSeed": 42,
    "outputGroups": ["newcontainer", "uuid", "zAll"],
    "outputRawOfGroup": [],
    "showAsList": [],
    "showAsSum": ["newcontainer"],
    "ignoreFromAll": ["zAll", "lang", "version"],
    "ignoreFromGroups": ["1_run_id", "2_thread_id", "startTime", "endTime", "bootTime"],
    "ignoreByGroup": {"newcontainer": ["newcontainer"]},
    "invalidators": {},
    "removeDuplicateContainers": False,
    "overlapFilter": "functionName",
    "openCSV": False,
    "warmupBuffer": 0,
    "passPayloads": False,
    "transitions": {},
}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4) + "\n")


config = json.loads((workloads / "config.json").read_text())
payloads = json.loads((here / "payloads.json").read_text())
# endpoints.sh writes endpoints.json. Without it, the Web Function and event function files have no endpoint.
endpoints = json.loads((here / "endpoints.json").read_text()) if (here / "endpoints.json").exists() else {}
prefix = config.get("prefix", "saaf")

# The workloads in payloads.json. The others have no experiments.
names = sorted(payloads)
missing = [name for name in names if not (workloads / name / "workload.json").is_file()]
if missing:
    raise SystemExit("payloads.json names workloads that do not exist: " + ", ".join(missing))

for name in names:
    for deployment, settings in config["deployments"].items():
        function = {
            "function": prefix + "-" + deployment + "-" + name.replace("_", "-"),
            "platform": "HTTP",
            "source": "../workloads",
            "endpoint": endpoints.get(deployment, {}).get(name, ""),
        }
        # A MicroVM's endpoint and auth token last only as long as the MicroVM, so microvm.sh
        # writes them when it starts one. FaaS Runner reads the token's header from headersFile.
        if settings["paradigm"] == "microvm":
            function["endpoint"] = ""
            function["headersFile"] = "workloads/.microvm/" + deployment + "/" + name + "/headers.json"
        write(here / "functions" / deployment / (name + ".json"), function)

    for experiment, runs, threads, iterations in EXPERIMENTS + [PILOT]:
        write(here / "experiments" / name / (experiment + ".json"), {
            "payloads": [payloads[name]["payload"]],
            "runs": runs,
            "threads": threads,
            "iterations": iterations,
            **SETTINGS,
            # FaaS Runner combines a single iteration's sheet with nothing, and says so.
            "combineSheets": iterations > 1,
        })

print("Wrote %d function files and %d experiment files for %d workloads." % (
    len(names) * len(config["deployments"]), len(names) * (len(EXPERIMENTS) + 1), len(names)))
