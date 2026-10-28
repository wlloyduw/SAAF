#!/bin/bash

# POST the test payload from config.json, or a JSON argument, to the Web Function.
#   ./run.sh
#   ./run.sh '{"name":"Ada"}'

cd "$(dirname "$0")" || exit

function=$(jq -r '.function_name' < ./config.json)
export AWS_REGION=$(jq -r '.region' < ./config.json)
json=${1:-$(jq -c '.test' < ./config.json)}

domain=$(aws lambda-web get-web-function-endpoint --function-name "$function" --endpoint-name dev --query domainName --output text)
response=$(curl -sS -X POST -H 'Content-Type: application/json' --data "$json" "https://$domain/")
echo "$response"
