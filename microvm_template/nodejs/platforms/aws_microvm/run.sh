#!/bin/bash

# POST the test payload from config.json, or a JSON argument, to a MicroVM running the image.
# With reuse_microvm set to true, a running or suspended MicroVM on the latest image version
# is reused. Otherwise, or when there is none, a new MicroVM is started from the snapshot.
#   ./run.sh
#   ./run.sh '{"name":"Ada"}'

cd "$(dirname "$0")" || exit

function=$(jq -r '.function_name' < ./config.json)
execution_role=$(jq -r '.execution_role' < ./config.json)
reuse=$(jq -r '.reuse_microvm' < ./config.json)
export AWS_REGION=$(jq -r '.region' < ./config.json)
json=${1:-$(jq -c '.test' < ./config.json)}

image=$(aws lambda-microvms get-microvm-image --image-identifier "$function") || exit 1
version=$(jq -r '.latestActiveImageVersion' <<< "$image")

microvm=""
if [[ $reuse == true ]]; then
	microvm=$(aws lambda-microvms list-microvms --image-identifier "$function" --image-version "$version" --output text \
		--query "items[?state=='RUNNING' || state=='SUSPENDED'].microvmId | [0]")
	if [[ $microvm == None ]]; then
		microvm=""
	fi
fi

if [[ -z $microvm ]]; then
	args=(--image-identifier "$(jq -r '.imageArn' <<< "$image")" --image-version "$version"
		--ingress-network-connectors "arn:aws:lambda:$AWS_REGION:aws:network-connector:aws-network-connector:ALL_INGRESS"
		--egress-network-connectors "arn:aws:lambda:$AWS_REGION:aws:network-connector:aws-network-connector:INTERNET_EGRESS"
		--idle-policy "$(jq -c '.idle_policy' < ./config.json)"
		--maximum-duration-in-seconds "$(jq -r '.maximum_duration' < ./config.json)")
	if [[ -n $execution_role ]]; then
		args+=(--execution-role-arn "$execution_role")
	fi
	microvm=$(aws lambda-microvms run-microvm "${args[@]}" --query microvmId --output text) || exit 1
	echo "Run: Started MicroVM $microvm" >&2
fi

# A new MicroVM is PENDING until the /run hook returns. A SUSPENDED MicroVM resumes when the request arrives.
while true; do
	read -r state endpoint < <(aws lambda-microvms get-microvm --microvm-identifier "$microvm" \
		--query '[state, endpoint]' --output text)
	case $state in
		RUNNING | SUSPENDED)
			break
			;;
		TERMINATING | TERMINATED)
			echo "Run: MicroVM $microvm is $state." >&2
			exit 1
			;;
	esac
	sleep 2
done

token=$(aws lambda-microvms create-microvm-auth-token --microvm-identifier "$microvm" \
	--expiration-in-minutes 5 --allowed-ports '[{"port":8080}]' --query 'authToken."X-aws-proxy-auth"' --output text) || exit 1

response=$(curl -sS --retry 3 -X POST -H 'Content-Type: application/json' -H "X-aws-proxy-auth: $token" \
	--data "$json" "https://${endpoint#https://}/")
echo "$response"
