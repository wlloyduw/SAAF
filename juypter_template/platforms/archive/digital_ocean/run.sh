#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')

json=$2

response=$(doctl serverless functions invoke "$function" -P /dev/stdin <<< $json)
echo "$response" | head -n -3 | head -c -2