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
echo "NOTE: If this is your first time deploying this function and it immediately fails to deploy, make an insignificant change (e.g. add a space to the end of a line) to your function and deploy again."
printf "y\n" | gcloud functions deploy $function --source=. --gen2 --allow-unauthenticated --entry-point $handler --runtime $runtime --timeout $timeout --region $region --trigger-http --project $project --memory $memory