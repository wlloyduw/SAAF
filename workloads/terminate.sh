#!/bin/bash

# Terminate every MicroVM running a workload's image, in every MicroVM deployment in config.json.
# Running MicroVMs are billed until they are suspended or terminated.
#   ./terminate.sh calc_service
#   ./terminate.sh all

cd "$(dirname "$0")" || exit

if [[ $# -ne 1 ]]; then
	echo "Usage: ./terminate.sh <workload|all>" >&2
	exit 1
fi

# The AWS CLI profile from config.json, when it names one, so every request goes to the same account.
profile=$(jq -r '.profile // empty' < ./config.json)
if [[ -n $profile ]]; then
	export AWS_PROFILE=$profile
fi

deployments=()
while IFS= read -r deployment; do
	deployments+=("$deployment")
done < <(jq -r '.deployments | to_entries[] | select(.value.paradigm == "microvm") | .key' < ./config.json)

platforms=()
for deployment in "${deployments[@]}"; do
	output=$(./package.sh "$1" "$deployment") || exit 1
	while IFS= read -r platform; do
		platforms+=("$platform")
	done <<< "$output"
done

for platform in "${platforms[@]}"; do
	"$platform/terminate.sh"
done
