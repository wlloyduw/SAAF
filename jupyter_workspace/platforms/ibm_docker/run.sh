#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')
json=$2

response=$(ibmcloud fn action invoke $function -b -P /dev/stdin --result <<< $json)
echo $response