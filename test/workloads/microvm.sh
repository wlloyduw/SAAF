#!/bin/bash

# Start, reauthorize, and stop the MicroVM that a workload's experiments call.
#   ./microvm.sh start <workload> [deployment]               Start a MicroVM from the workload's image
#   ./microvm.sh token <workload> [deployment]               Replace its auth token
#   ./microvm.sh stop <workload> [deployment] [terminate|suspend]
#
# The deployment is a MicroVM deployment in ../../workloads/config.json, microvm by default.
# start runs a MicroVM from the image's latest version, waits for its /run hook to finish, and writes
# .microvm/<deployment>/<workload>/function.json: the workload's function file with the MicroVM's
# endpoint. FaaS Runner sends the auth token in headers.json, next to it, with every request. A token
# lasts 60 minutes at most, so run.sh calls token every 45 minutes while an experiment runs.
#
# A running MicroVM is billed until it is stopped, so stop terminates it by default. A suspended one
# resumes on its next request. Either way, it ends after MAXIMUM_DURATION seconds, 8 hours at most.
#
# MicroVMs cannot be tagged for billing, so each start, suspend, and termination is appended to
# history/microvms.jsonl with Lambda's description of the MicroVM, which has its startedAt and, once it
# is terminated, terminatedAt. EXPERIMENT, which run.sh sets, labels each record. usage.sh collects the
# same times for every MicroVM of every image, including ones started some other way.

cd "$(dirname "$0")" || exit

MAXIMUM_DURATION=${MAXIMUM_DURATION:-28800}
# An experiment's requests can take minutes each, so the MicroVM waits 15 idle minutes before suspending.
IDLE_POLICY='{"autoResumeEnabled":true,"maxIdleDurationSeconds":900,"suspendedDurationSeconds":600}'

command=$1
workload=$2
deployment=${3:-microvm}
config=../../workloads/config.json
log=./history/microvms.jsonl

if [[ $command != start && $command != token && $command != stop ]] || [[ ! -f ../../workloads/$workload/workload.json ]]; then
	echo "Usage: ./microvm.sh <start|token|stop> <workload> [deployment] [terminate|suspend]" >&2
	exit 1
fi
if [[ $(jq -r --arg d "$deployment" '.deployments[$d].paradigm' < "$config") != microvm ]]; then
	echo "MicroVM: $deployment is not a MicroVM deployment in workloads/config.json." >&2
	exit 1
fi

profile=$(jq -r '.profile // empty' < "$config")
if [[ -n $profile ]]; then
	export AWS_PROFILE=$profile
fi
export AWS_REGION
AWS_REGION=$(jq -r '.region' < "$config")
prefix=$(jq -r '.prefix // "saaf"' < "$config")
execution_role=$(jq -r --arg d "$deployment" '.deployments[$d].execution_role // empty' < "$config")
state=./.microvm/$deployment/$workload

token() {
	local microvm
	microvm=$(cat "$state/microvm") || return 1
	aws lambda-microvms create-microvm-auth-token --microvm-identifier "$microvm" --expiration-in-minutes 60 \
		--allowed-ports '[{"port":8080}]' --query authToken --output json > "$state/headers.json.new" || return 1
	mv "$state/headers.json.new" "$state/headers.json"
}

# Append a record of event $1 for MicroVM $2, with Lambda's description of it in the JSON object $3,
# or null when there is none.
record() {
	local description=$3
	if [[ -z $description ]] || ! jq . <<< "$description" > /dev/null 2>&1; then
		description=null
	fi
	mkdir -p "$(dirname "$log")"
	jq -c -n --arg event "$1" --arg id "$2" --arg deployment "$deployment" --arg workload "$workload" \
		--arg experiment "${EXPERIMENT:-manual}" --arg recordedAt "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
		--argjson microvm "$description" \
		'{event: $event, microvmId: $id, deployment: $deployment, workload: $workload, experiment: $experiment,
			recordedAt: $recordedAt, microvm: $microvm}' >> "$log"
}

case $command in
	start)
		if [[ -f $state/microvm ]]; then
			echo "MicroVM: $(cat "$state/microvm") is already started for $workload. Stop it first." >&2
			exit 1
		fi
		if [[ ! -f ./functions/$deployment/$workload.json ]]; then
			echo "MicroVM: functions/$deployment/$workload.json is missing. Run generate.py." >&2
			exit 1
		fi
		mkdir -p "$state"

		# MicroVM commands identify an image by its ARN, not its name.
		account=$(aws sts get-caller-identity --query Account --output text) || exit 1
		image="arn:aws:lambda:$AWS_REGION:$account:microvm-image:$prefix-$deployment-${workload//_/-}"
		version=$(aws lambda-microvms get-microvm-image --image-identifier "$image" \
			--query latestActiveImageVersion --output text) || exit 1

		args=(--image-identifier "$image" --image-version "$version"
			--ingress-network-connectors "arn:aws:lambda:$AWS_REGION:aws:network-connector:aws-network-connector:ALL_INGRESS"
			--egress-network-connectors "arn:aws:lambda:$AWS_REGION:aws:network-connector:aws-network-connector:INTERNET_EGRESS"
			--idle-policy "$IDLE_POLICY" --maximum-duration-in-seconds "$MAXIMUM_DURATION")
		if [[ -n $execution_role ]]; then
			args+=(--execution-role-arn "$execution_role")
		fi
		description=$(aws lambda-microvms run-microvm "${args[@]}" --output json) || {
			rm -rf "$state"
			exit 1
		}
		microvm=$(jq -r '.microvmId' <<< "$description")
		echo "$microvm" > "$state/microvm"
		record started "$microvm" "$description"
		echo "MicroVM: Started $microvm from $image version $version" >&2

		# A new MicroVM is PENDING until its /run hook returns.
		for ((i = 0; ; i++)); do
			description=$(aws lambda-microvms get-microvm --microvm-identifier "$microvm" --output json)
			status=$(jq -r '.state // empty' <<< "$description" 2> /dev/null)
			if [[ $status == RUNNING || $status == SUSPENDED ]]; then
				break
			fi
			if [[ $status == TERMINATING || $status == TERMINATED || $i -ge 150 ]]; then
				echo "MicroVM: $microvm is ${status:-unknown} after $((i * 2)) seconds. Stopping it." >&2
				"$0" stop "$workload" "$deployment"
				exit 1
			fi
			sleep 2
		done
		record "$(tr '[:upper:]' '[:lower:]' <<< "$status")" "$microvm" "$description"

		# The MicroVM is billed from here on, so a failure terminates it.
		endpoint=$(jq -r '.endpoint' <<< "$description")
		if ! token || ! jq --arg endpoint "https://${endpoint#https://}/" '.endpoint = $endpoint' \
			"./functions/$deployment/$workload.json" > "$state/function.json"; then
			echo "MicroVM: Could not authorize $microvm. Stopping it." >&2
			"$0" stop "$workload" "$deployment"
			exit 1
		fi
		echo "MicroVM: $microvm is $status at https://${endpoint#https://}/" >&2
		;;
	token)
		token || exit 1
		;;
	stop)
		if [[ ! -f $state/microvm ]]; then
			echo "MicroVM: No MicroVM is started for $workload." >&2
			exit 0
		fi
		microvm=$(cat "$state/microvm")
		if [[ ${4:-terminate} == suspend ]]; then
			aws lambda-microvms suspend-microvm --microvm-identifier "$microvm" > /dev/null || exit 1
			record suspended "$microvm" "$(aws lambda-microvms get-microvm --microvm-identifier "$microvm" --output json)"
			echo "MicroVM: Suspended $microvm" >&2
			exit 0
		fi

		aws lambda-microvms terminate-microvm --microvm-identifier "$microvm" > /dev/null || exit 1
		rm -rf "$state"
		# Wait up to 5 minutes for TERMINATED, so the record has Lambda's terminatedAt.
		for ((i = 0; i < 60; i++)); do
			description=$(aws lambda-microvms get-microvm --microvm-identifier "$microvm" --output json)
			if [[ $(jq -r '.state // empty' <<< "$description" 2> /dev/null) == TERMINATED ]]; then
				break
			fi
			sleep 5
		done
		if [[ $(jq -r '.state // empty' <<< "$description" 2> /dev/null) == TERMINATED ]]; then
			record terminated "$microvm" "$description"
			echo "MicroVM: Terminated $microvm" >&2
		else
			record terminating "$microvm" "$description"
			echo "MicroVM: $microvm is still terminating. usage.sh records when it ends." >&2
		fi
		;;
esac
