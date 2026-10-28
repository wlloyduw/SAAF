#!/bin/bash

# Build and deploy the Web Function described in config.json.
# Each deploy creates a revision, so revisions no longer serving traffic are deleted.

cd "$(dirname "$0")" || exit
./build.sh

echo "Publish: Loading config..."
function=$(jq -r '.function_name' < ./config.json)
timeout=$(jq -r '.timeout' < ./config.json)
concurrency=$(jq -r '.max_concurrency_per_environment' < ./config.json)
role=$(jq -r '.role' < ./config.json)
export AWS_REGION=$(jq -r '.region' < ./config.json)

# Web Functions do not set AWS_LAMBDA_FUNCTION_NAME, so SAAF reads SAAF_FUNCTION_NAME instead.
args=(--name "$function" --code ./.build --create --timeout-seconds "$timeout"
	--max-concurrency-per-environment "$concurrency" --env "SAAF_FUNCTION_NAME=$function")
if [[ -n $role ]]; then
	args+=(--execution-role-arn "$role")
fi
while read -r pair; do
	args+=(--env "$pair")
done < <(jq -r '.env | to_entries[] | "\(.key)=\(.value)"' < ./config.json)

echo "Publish: Deploying function..."
aws lambda-web deploy "${args[@]}" || exit 1

echo "Publish: Deleting old revisions..."
# The newest revision is always kept because the endpoint may not have switched to it yet.
active=$(aws lambda-web get-web-function-endpoint --function-name "$function" --endpoint-name dev --query 'revisionWeights[].revisionId' --output text)
for revision in $(aws lambda-web list-web-function-revisions --function-name "$function" --query 'sort_by(revisions, &createdAt)[:-1].revisionId' --output text); do
	if [[ " $active " != *" $revision "* ]]; then
		aws lambda-web delete-web-function-revision --function-name "$function" --revision-id "$revision"
	fi
done

echo "Publish: Function deployed!"
