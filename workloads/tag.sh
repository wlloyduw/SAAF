#!/bin/bash

# Tag each deployed workload so AWS billing can attribute its costs: config.json's tags, plus the
# workload's deployment, paradigm, and workload name. publish.sh runs this after each deploy. Tagging
# again replaces the values of existing keys, so it is safe to repeat.
#   ./tag.sh calc_service web
#   ./tag.sh all all
#
# Each paradigm tags a different resource:
#   event     The Lambda function. Its function URL's requests are billed to the function.
#   web       The Web Function.
#   microvm   The MicroVM image. MicroVMs themselves cannot be tagged, so test/workloads/microvm.sh
#             and test/workloads/usage.sh record when each one ran.
#
# AWS billing only uses a tag after it is activated as a cost allocation tag, and only for costs from
# then on. See test/workloads/README.md.

cd "$(dirname "$0")" || exit

if [[ $# -ne 2 ]]; then
	echo "Usage: ./tag.sh <workload|all> <deployment|all>" >&2
	exit 1
fi

if [[ $1 == all ]]; then
	workloads=()
	for file in ./*/workload.json; do
		workloads+=("$(basename "$(dirname "$file")")")
	done
elif [[ -f ./$1/workload.json ]]; then
	workloads=("$1")
else
	echo "Tag: $1 is not a workload. Each workload is a folder with a workload.json." >&2
	exit 1
fi

deployments=()
if [[ $2 == all ]]; then
	while IFS= read -r deployment; do
		deployments+=("$deployment")
	done < <(jq -r '.deployments | keys_unsorted[]' < ./config.json)
elif jq -e --arg deployment "$2" '.deployments[$deployment]' < ./config.json > /dev/null; then
	deployments=("$2")
else
	echo "Tag: $2 is not a deployment in config.json." >&2
	exit 1
fi

profile=$(jq -r '.profile // empty' < ./config.json)
if [[ -n $profile ]]; then
	export AWS_PROFILE=$profile
fi
export AWS_REGION
AWS_REGION=$(jq -r '.region' < ./config.json)
prefix=$(jq -r '.prefix // "saaf"' < ./config.json)
account=$(aws sts get-caller-identity --query Account --output text) || exit 1

# Tag the resource named $2 for paradigm $1 with the JSON object $3.
tag_resource() {
	local arn
	case $1 in
		event)
			aws lambda tag-resource --resource "arn:aws:lambda:$AWS_REGION:$account:function:$2" --tags "$3"
			;;
		web)
			arn=$(aws lambda-web get-web-function --function-name "$2" --query functionArn --output text) &&
				aws lambda-web tag-resource --resource "$arn" --tags "$3"
			;;
		microvm)
			aws lambda-microvms tag-resource --resource "arn:aws:lambda:$AWS_REGION:$account:microvm-image:$2" --tags "$3"
			;;
	esac
}

failed=0
for deployment in "${deployments[@]}"; do
	paradigm=$(jq -r --arg deployment "$deployment" '.deployments[$deployment].paradigm' < ./config.json)
	for workload in "${workloads[@]}"; do
		name="$prefix-$deployment-${workload//_/-}"
		tags=$(jq -c --arg deployment "$deployment" --arg paradigm "$paradigm" --arg workload "$workload" \
			'(.tags // {}) + {deployment: $deployment, paradigm: $paradigm, workload: $workload}' < ./config.json)
		if tag_resource "$paradigm" "$name" "$tags"; then
			echo "Tag: Tagged $name with $tags"
		else
			echo "Tag: Could not tag $name. Is it deployed?" >&2
			failed=$((failed + 1))
		fi
	done
done

if [[ $failed -gt 0 ]]; then
	echo "Tag: $failed could not be tagged." >&2
	exit 1
fi
