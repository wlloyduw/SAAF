#!/bin/bash

location=$1
cd "$location" || exit

dynamic_url=$(jq '.dynamic_url' < ./config.json | tr -d '"')
code=$(cat ./.build/code.txt)

json=$2

json=$(echo $2 | jq '.function |= "'$code'"')
#echo $json

echo $(curl -X POST -H "Content-Type: application/json" \
    -d "$json" -s \
    $dynamic_url)