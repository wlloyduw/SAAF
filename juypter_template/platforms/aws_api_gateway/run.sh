#!/bin/bash


location=$1
cd "$location" || exit

function_url=$(jq '.function_url' < ./config.json | tr -d '"')

json=$2

echo $(curl -X POST -H "Content-Type: application/json" -d "$json" -s $function_url)