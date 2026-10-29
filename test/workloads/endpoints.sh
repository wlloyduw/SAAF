#!/bin/bash

# Look up the HTTP endpoint of every Web Function and event function in ../../workloads/config.json,
# write them to endpoints.json, and regenerate the function files. It only reads from AWS. Run it
# after publishing, since each event function gets its function URL when it is first published.
# MicroVM endpoints are left out, since microvm.sh writes one each time it starts a MicroVM.
#   ./endpoints.sh

cd "$(dirname "$0")" || exit
config=../../workloads/config.json

profile=$(jq -r '.profile // empty' < "$config")
if [[ -n $profile ]]; then
	export AWS_PROFILE=$profile
fi
export AWS_REGION
AWS_REGION=$(jq -r '.region' < "$config")
prefix=$(jq -r '.prefix // "saaf"' < "$config")

endpoints=$(cat ./endpoints.json 2> /dev/null || echo '{}')
missing=0
while read -r deployment paradigm; do
	for file in ../../workloads/*/workload.json; do
		workload=$(basename "$(dirname "$file")")
		function="$prefix-$deployment-${workload//_/-}"
		case $paradigm in
			web)
				domain=$(aws lambda-web get-web-function-endpoint --function-name "$function" --endpoint-name dev \
					--query domainName --output text 2> /dev/null)
				url=${domain:+https://$domain/}
				;;
			event)
				url=$(aws lambda get-function-url-config --function-name "$function" --query FunctionUrl \
					--output text 2> /dev/null)
				;;
		esac
		if [[ -z $url ]]; then
			echo "Endpoints: $function has no endpoint. Publish it first." >&2
			missing=$((missing + 1))
		fi
		endpoints=$(jq --arg d "$deployment" --arg w "$workload" --arg url "$url" '.[$d][$w] = $url' <<< "$endpoints")
	done
done < <(jq -r '.deployments | to_entries[] | select(.value.paradigm != "microvm") | "\(.key) \(.value.paradigm)"' < "$config")

echo "$endpoints" > ./endpoints.json
echo "Endpoints: Wrote endpoints.json, with $missing missing."
python3 ./generate.py
