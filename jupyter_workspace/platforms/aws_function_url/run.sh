#!/bin/bash

location=$1
cd "$location" || exit

url=$(jq '.function_url' < ./config.json | tr -d '"')

json=$2

response=$(aws lambda invoke --invocation-type RequestResponse --cli-binary-format raw-in-base64-out --cli-read-timeout 900 --function-name "$function" --payload "$json" /dev/stdout)
echo "$response" | head -n -3 | head -c -2