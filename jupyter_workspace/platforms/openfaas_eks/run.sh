#!/bin/bash

gateway=$(jq '.gateway' < ./config.json | tr -d '"')
function=$(jq '.function_name' < ./config.json | tr -d '"')
json=$2

curl -X POST $gateway/function/$function \
	-H 'Content-Type: application/json' \
	-d $json