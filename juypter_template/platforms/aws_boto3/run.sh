#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')
profile=$(jq '.profile' < ./config.json | tr -d '"')
export AWS_PROFILE=$profile

json=$2

response=$(python3 run.py "$function" "$json")
echo "$response"