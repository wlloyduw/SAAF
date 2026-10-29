#!/bin/bash

# Run FaaS Runner experiments for workloads on deployments, one experiment at a time.
#   ./run.sh mandelbrot web                     Every experiment except pilot, in order
#   ./run.sh all event-2048
#   ./run.sh mandelbrot all pilot               Only the pilot
#   ./run.sh mandelbrot microvm sequential-0100 burst-0010
#
# Results go to history/<deployment>/<workload>, with FaaS Runner's output for each experiment in
# <experiment>.log. Deployments without an endpoint in their function file are skipped; run
# endpoints.sh after publishing. For a MicroVM deployment, each experiment gets its own MicroVM from
# microvm.sh, with its auth token replaced every 45 minutes, and the MicroVM is terminated afterward,
# including when the script is interrupted.
#
# history/experiments.csv gets a row for each experiment, with its UTC start and finish times, to match
# experiments to AWS's hourly billing data, and the MicroVM it called. microvm.sh records each MicroVM's
# own start and termination times in history/microvms.jsonl.

cd "$(dirname "$0")" || exit
config=../../workloads/config.json

# Each request in a burst has its own connection, and macOS allows a process 256 open files by default.
ulimit -n 4096 2> /dev/null || ulimit -n "$(ulimit -Hn)" 2> /dev/null
if [[ $(ulimit -n) != unlimited && $(ulimit -n) -lt 2048 ]]; then
	echo "Run: Only $(ulimit -n) open files are allowed, too few for burst-1000. Raise the hard limit first." >&2
	exit 1
fi

if [[ $# -lt 2 ]]; then
	echo "Usage: ./run.sh <workload|all> <deployment|all> [experiment...]" >&2
	exit 1
fi

if [[ $1 == all ]]; then
	workloads=()
	for folder in ./experiments/*/; do
		workloads+=("$(basename "$folder")")
	done
elif [[ -d ./experiments/$1 ]]; then
	workloads=("$1")
else
	echo "Run: $1 has no experiments. Run generate.py." >&2
	exit 1
fi

deployments=()
if [[ $2 == all ]]; then
	while IFS= read -r deployment; do
		deployments+=("$deployment")
	done < <(jq -r '.deployments | keys_unsorted[]' < "$config")
elif jq -e --arg d "$2" '.deployments[$d]' < "$config" > /dev/null; then
	deployments=("$2")
else
	echo "Run: $2 is not a deployment in workloads/config.json." >&2
	exit 1
fi

shift 2
experiments=("$@")
if [[ ${#experiments[@]} -eq 0 ]]; then
	for file in "./experiments/${workloads[0]}"/sequential-*.json "./experiments/${workloads[0]}"/burst-*.json; do
		experiments+=("$(basename "$file" .json)")
	done
fi

experiments_log=./history/experiments.csv
mkdir -p ./history
if [[ ! -f $experiments_log ]]; then
	echo "deployment,workload,experiment,startedAt,finishedAt,status,successfulRequests,failedRequests,timedOutRequests,microvmId" \
		> "$experiments_log"
fi

# The experiment that is running, as deployment/workload/experiment, when it started, and its MicroVM.
current=""
current_started=""
current_microvm=""

# Append the running experiment's row to experiments.csv, with status $1 and the counts from its log.
finish_row() {
	local log=./history/$current.log successful failed timed_out
	successful=$(grep -o 'Successful Runs: [0-9]*' "$log" 2> /dev/null | awk '{sum += $3} END {print sum + 0}')
	failed=$(grep -c '^Run [0-9]*\.[0-9]* failed: ' "$log" 2> /dev/null)
	timed_out=$(grep -c ' timed out after [0-9]* seconds\.$' "$log" 2> /dev/null)
	echo "${current//\//,},$current_started,$(date -u '+%Y-%m-%dT%H:%M:%SZ'),$1,$successful,${failed:-0},${timed_out:-0},$current_microvm" \
		>> "$experiments_log"
	current=""
}

# The process replacing a MicroVM's token, and the workload and deployment of the MicroVM that is running.
refresher=""
running=()
stop_microvm() {
	if [[ -n $refresher ]]; then
		kill "$refresher" 2> /dev/null
		refresher=""
	fi
	if [[ ${#running[@]} -gt 0 ]]; then
		./microvm.sh stop "${running[@]}"
		running=()
	fi
}

# When the script is interrupted, stop FaaS Runner's process and the MicroVM, and record the experiment.
runner=""
cleanup() {
	if [[ -n $runner ]]; then
		kill "$runner" 2> /dev/null
		runner=""
	fi
	stop_microvm
	if [[ -n $current ]]; then
		finish_row interrupted
	fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

for deployment in "${deployments[@]}"; do
	paradigm=$(jq -r --arg d "$deployment" '.deployments[$d].paradigm' < "$config")
	for workload in "${workloads[@]}"; do
		function=./workloads/functions/$deployment/$workload.json
		if [[ $paradigm != microvm && -z $(jq -r '.endpoint' < "./functions/$deployment/$workload.json") ]]; then
			echo "Run: Skipping $deployment/$workload, which has no endpoint." >&2
			continue
		fi
		out=./history/$deployment/$workload
		mkdir -p "$out"

		for experiment in "${experiments[@]}"; do
			if [[ ! -f ./experiments/$workload/$experiment.json ]]; then
				echo "Run: $workload has no experiment $experiment." >&2
				continue
			fi

			# The row's times include starting and stopping the experiment's MicroVM, which is billed too.
			current=$deployment/$workload/$experiment
			current_started=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
			current_microvm=""
			# microvm.sh labels its records with the experiment.
			export EXPERIMENT=$experiment

			if [[ $paradigm == microvm ]]; then
				if ! ./microvm.sh start "$workload" "$deployment"; then
					# microvm.sh terminates a MicroVM it could not start. Stopping again is harmless.
					./microvm.sh stop "$workload" "$deployment"
					finish_row "microvm did not start"
					continue
				fi
				running=("$workload" "$deployment")
				current_microvm=$(cat "./.microvm/$deployment/$workload/microvm")
				function=./workloads/.microvm/$deployment/$workload/function.json
				(while sleep 2700; do ./microvm.sh token "$workload" "$deployment"; done) &
				refresher=$!
			fi

			echo "Run: $deployment/$workload $experiment started at $(date '+%H:%M:%S')" >&2
			# FaaS Runner loads its tools from the test folder, and the files' paths are relative to it.
			# It runs in the background because bash runs traps during wait, not while a command runs.
			(cd .. && exec python3 ./faas_runner.py -f "$function" -e "./workloads/experiments/$workload/$experiment.json" \
				-o "./workloads/history/$deployment/$workload") > "$out/$experiment.log" 2>&1 &
			runner=$!
			wait "$runner"
			runner=""
			# FaaS Runner reports the successful requests in each iteration, and why it stopped early.
			echo "Run: $deployment/$workload $experiment finished at $(date '+%H:%M:%S')." \
				"Successful requests: $(grep -o 'Successful Runs: [0-9]*' "$out/$experiment.log" | cut -d' ' -f3 | tr '\n' ' ')" >&2
			grep -o 'STOPPING EXPERIMENT: .*' "$out/$experiment.log" | sed 's/^/Run: /' >&2

			stop_microvm
			finish_row finished
		done
	done
done
