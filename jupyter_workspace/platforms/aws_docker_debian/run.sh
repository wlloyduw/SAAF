#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')
profile=$(jq '.profile' < ./config.json | tr -d '"')
export AWS_PROFILE=$profile

json=$2

response=$(aws lambda invoke --invocation-type RequestResponse --cli-read-timeout 900 --function-name "$function" --payload "$json" /dev/stdout)
echo "$response" | head -n -3 | head -c -2