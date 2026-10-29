#!/bin/bash

# Send the test payload, the workload's defaults, or a JSON argument to a deployed workload and print
# the response. Uses the stage publish.sh made, so run.sh can be called many times at once.
#   ./run.sh calc_service event-2048
#   ./run.sh calc_service microvm '{"threads":2}'

cd "$(dirname "$0")" || exit

if [[ $# -lt 2 || $1 == all || $2 == all ]]; then
	echo "Usage: ./run.sh <workload> <deployment> [json]" >&2
	exit 1
fi

paradigm=$(jq -r --arg deployment "$2" '.deployments[$deployment].paradigm // empty' < ./config.json)
if [[ -z $paradigm ]]; then
	echo "Run: $2 is not a deployment in config.json." >&2
	exit 1
fi

# The AWS CLI profile from config.json, when it names one, so every request goes to the same account.
profile=$(jq -r '.profile // empty' < ./config.json)
if [[ -n $profile ]]; then
	export AWS_PROFILE=$profile
fi

platform=$PWD/.build/$2/$1/platforms/aws_$paradigm
if [[ ! -d $platform ]]; then
	platform=$(./package.sh "$1" "$2") || exit 1
fi
"$platform/run.sh" "${@:3}"
