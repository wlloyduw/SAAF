#!/bin/bash

location=$1
cd "$location" || exit

echo "Publish: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
memory=$(jq '.memory' < ./config.json | tr -d '"')
runtime=$(jq '.runtime' < ./config.json | tr -d '"')

cd ./.build || exit

echo "Publish: Deploying function..."
ibmcloud fn action update $function --kind $runtime --memory $memory index.zip