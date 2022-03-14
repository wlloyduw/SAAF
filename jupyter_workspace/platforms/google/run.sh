#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')
json=$(jq -c '.test_payload' < ./config.json)

gcloud functions call $function --data $json --format json | jq -r -c '.result'