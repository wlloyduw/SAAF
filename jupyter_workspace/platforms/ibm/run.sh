#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')
json=$(jq '.test_payload' < ./config.json | tr -d '"' | tr -d '{' | tr -d '}' | tr -d ':')

ibmcloud fn action invoke $function -b -p $json --result | tail -n +2 | jq -r -c '.response.result'