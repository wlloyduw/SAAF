#!/bin/bash

# Invoke the function with the test payload from config.json, or a JSON argument, and print the response.
#   ./run.sh
#   ./run.sh '{"threads":2}'

cd "$(dirname "$0")" || exit

function=$(jq -r '.function_name' < ./config.json)
export AWS_REGION=$(jq -r '.region' < ./config.json)
json=${1:-$(jq -c '.test' < ./config.json)}

# The CLI's read timeout matches Lambda's 900 second limit, so a long invocation is not retried.
response=$(mktemp)
aws lambda invoke --function-name "$function" --cli-binary-format raw-in-base64-out --cli-read-timeout 900 \
	--payload "$json" "$response" > /dev/null || exit 1
cat "$response"
echo
rm -f "$response"
