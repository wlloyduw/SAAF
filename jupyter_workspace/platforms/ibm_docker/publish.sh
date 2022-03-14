#!/bin/bash

location=$1
cd "$location" || exit

echo "Publish: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
memory=$(jq '.memory' < ./config.json | tr -d '"')

cd ./.build || exit

echo "Publish: Pushing Docker Image..."
dockerHubUsername=$(docker info | sed '/Username:/!d;s/.* //');
docker tag ${function}:latest ${dockerHubUsername}/saaf-functions:${function}
docker push ${dockerHubUsername}/saaf-functions:${function} >> ../${function}_ibm_build_progress.txt

echo "Publish: Deploying function..."
ibmcloud fn action update $function --docker ${dockerHubUsername}/saaf-functions:${function} --memory $memory index.zip