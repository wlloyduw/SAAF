#!/bin/bash

location=$1
cd "$location" || exit

echo "Publish: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
memory=$(jq '.memory' < ./config.json | tr -d '"')
handler=$(jq '.handler' < ./config.json | tr -d '"')
runtime=$(jq '.runtime' < ./config.json | tr -d '"')
timeout=$(jq '.timeout' < ./config.json | tr -d '"')
project=$(jq '.project' < ./config.json | tr -d '"')
region=$(jq '.region' < ./config.json | tr -d '"')

cd ./.build || exit

echo "Publish: Deploying function..."
printf "y\n" | gcloud functions deploy $function --source=. --allow-unauthenticated --entry-point $handler --runtime $runtime --timeout $timeout --trigger-http --memory $memory