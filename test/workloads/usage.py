#!/usr/bin/env python3

#
# Collect the usage AWS bills these experiments for, from records other than the bill, to check the
# bill against. It only reads from AWS.
#
#   history/microvm-lifetimes.csv  Every MicroVM of every workload's image, with when Lambda started
#                                  and terminated it, how long it ran, and how much of that was in
#                                  the time window.
#   history/event-usage.csv        Each event function's invocations in the time window, and the
#                                  duration Lambda billed them for, from the REPORT line Lambda logs
#                                  after each invocation.
#
# Web Functions have no such record, so their usage comes from the bill alone. See README.md.
#
#   python3 usage.py                 The time window runs from the first experiment in
#                                    history/experiments.csv to an hour after the last one.
#   python3 usage.py <start> <end>   UTC times, such as 2026-11-02T00:00:00Z.
#
import csv
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import time

here = pathlib.Path(__file__).resolve().parent
workloads = here.parents[1] / "workloads"
history = here / "history"
config = json.loads((workloads / "config.json").read_text())
prefix = config.get("prefix", "saaf")
names = sorted(path.parent.name for path in workloads.glob("*/workload.json"))

env = dict(os.environ, AWS_REGION=config["region"])
if config.get("profile"):
    env["AWS_PROFILE"] = config["profile"]


def aws(*args):
    """Run an AWS CLI command and return its JSON output, or raise RuntimeError with its error."""
    result = subprocess.run(["aws", *args, "--output", "json"], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout) if result.stdout.strip() else {}


def parse(timestamp):
    """A UTC datetime from an ISO 8601 time, such as the AWS CLI prints."""
    timestamp = timestamp.replace("Z", "+00:00")
    # Python 3.8 reads 3 or 6 digits of fractional seconds, so pad or cut to 6.
    timestamp = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], timestamp)
    moment = datetime.datetime.fromisoformat(timestamp)
    return moment if moment.tzinfo else moment.replace(tzinfo=datetime.timezone.utc)


def window():
    if len(sys.argv) == 3:
        return parse(sys.argv[1]), parse(sys.argv[2])
    with open(history / "experiments.csv") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise SystemExit("history/experiments.csv has no experiments. Give a start and end time.")
    return (min(parse(row["startedAt"]) for row in rows),
            max(parse(row["finishedAt"]) for row in rows) + datetime.timedelta(hours=1))


def microvms(start, end):
    rows, running = [], []
    for deployment, settings in config["deployments"].items():
        if settings["paradigm"] != "microvm":
            continue
        account = aws("sts", "get-caller-identity")["Account"]
        for name in names:
            image = "arn:aws:lambda:%s:%s:microvm-image:%s-%s-%s" % (
                config["region"], account, prefix, deployment, name.replace("_", "-"))
            try:
                items = aws("lambda-microvms", "list-microvms", "--image-identifier", image).get("items", [])
            except RuntimeError as error:
                print("MicroVMs: Could not list %s: %s" % (image, error), file=sys.stderr)
                continue
            for item in items:
                described = aws("lambda-microvms", "get-microvm", "--microvm-identifier", item["microvmId"])
                started = parse(described["startedAt"])
                ended = parse(described["terminatedAt"]) if described.get("terminatedAt") else None
                if ended is None:
                    running.append(item["microvmId"])
                # Time running within the window. A MicroVM still running counts up to now.
                stop = min(ended or datetime.datetime.now(datetime.timezone.utc), end)
                overlap = max(0.0, (stop - max(started, start)).total_seconds())
                rows.append({
                    "deployment": deployment, "workload": name, "microvmId": item["microvmId"],
                    "imageVersion": described.get("imageVersion", ""), "state": described.get("state", ""),
                    "startedAt": described["startedAt"], "terminatedAt": described.get("terminatedAt") or "",
                    "seconds": round((ended - started).total_seconds(), 3) if ended else "",
                    "secondsInWindow": round(overlap, 3),
                    "maximumDurationInSeconds": described.get("maximumDurationInSeconds", ""),
                })
    return rows, running


# Lambda logs a REPORT line after each invocation, with the duration it billed.
QUERY = ('filter @type = "REPORT" | stats count(*) as invocations, sum(@billedDuration) as billedMs, '
         'sum(@duration) as durationMs, sum(@initDuration) as initMs, count(@initDuration) as coldStarts, '
         'max(@maxMemoryUsed) as maxMemoryUsedBytes')


def events(start, end):
    rows, missing = [], []
    for deployment, settings in config["deployments"].items():
        if settings["paradigm"] != "event":
            continue
        for name in names:
            function = "%s-%s-%s" % (prefix, deployment, name.replace("_", "-"))
            group = "/aws/lambda/" + function
            try:
                query = aws("logs", "start-query", "--log-group-name", group, "--start-time", str(int(start.timestamp())),
                            "--end-time", str(int(end.timestamp())), "--query-string", QUERY)["queryId"]
            except RuntimeError as error:
                missing.append(function)
                print("Events: Could not query %s: %s" % (group, error), file=sys.stderr)
                continue
            for _ in range(300):
                result = aws("logs", "get-query-results", "--query-id", query)
                if result["status"] in ("Complete", "Failed", "Cancelled", "Timeout"):
                    break
                time.sleep(1)
            if result["status"] != "Complete":
                missing.append(function)
                print("Events: The query of %s ended %s." % (group, result["status"]), file=sys.stderr)
                continue
            values = {field["field"]: field["value"] for field in (result["results"] or [[]])[0]}
            billed = float(values.get("billedMs") or 0) / 1000
            rows.append({
                "deployment": deployment, "workload": name, "function": function,
                "memoryMB": settings["memory"], "invocations": int(float(values.get("invocations") or 0)),
                "coldStarts": int(float(values.get("coldStarts") or 0)),
                "billedSeconds": round(billed, 3),
                "durationSeconds": round(float(values.get("durationMs") or 0) / 1000, 3),
                "initSeconds": round(float(values.get("initMs") or 0) / 1000, 3),
                "gbSeconds": round(billed * settings["memory"] / 1024, 3),
                "maxMemoryUsedMB": round(float(values.get("maxMemoryUsedBytes") or 0) / 1e6),
            })
    return rows, missing


def write(path, rows):
    if rows:
        with open(path, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print("Wrote %s, %d rows." % (path.relative_to(here), len(rows)))


start, end = window()
print("Window: %s to %s" % (start.isoformat(), end.isoformat()))
history.mkdir(exist_ok=True)

lifetimes, running = microvms(start, end)
write(history / "microvm-lifetimes.csv", lifetimes)
for deployment in sorted({row["deployment"] for row in lifetimes}):
    mine = [row for row in lifetimes if row["deployment"] == deployment]
    print("%s: %d MicroVMs ran %.2f hours in the window." % (
        deployment, sum(row["secondsInWindow"] > 0 for row in mine), sum(row["secondsInWindow"] for row in mine) / 3600))
if running:
    print("WARNING: %d MicroVMs have not terminated and are still billed: %s" % (len(running), " ".join(running)))

usage, missing = events(start, end)
write(history / "event-usage.csv", usage)
for deployment in sorted({row["deployment"] for row in usage}):
    mine = [row for row in usage if row["deployment"] == deployment]
    print("%s: %d invocations, %.0f GB-seconds billed." % (
        deployment, sum(row["invocations"] for row in mine), sum(row["gbSeconds"] for row in mine)))
if missing:
    print("WARNING: No REPORT lines for %d functions, so their usage is only in the bill: %s" % (len(missing), " ".join(missing)))
