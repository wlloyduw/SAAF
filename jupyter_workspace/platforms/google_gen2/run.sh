#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')
region=$(jq -c '.region' < ./config.json)

json=$2

gcloud beta functions call $function --gen2 --data="$json" --format json | jq -r '.'