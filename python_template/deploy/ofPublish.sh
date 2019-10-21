#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Python functions onto AWS Lambda, Google Cloud Functions, IBM
# Cloud Functions, and Azure Functions.
#
# Each platform's default function is defined in the platforms folder. These are copied into the source folder as index.js
# and deployed onto each platform accordingly. Developers should write their function in the function.js file. 
# All source files should be in the src folder and dependencies defined in package.json.
#
# This script requires each platform's CLI to be installed and properly configured to update functions.
# AWS CLI: apt install awscli 
# Google Cloud CLI: https://cloud.google.com/sdk/docs/quickstarts
# IBM Cloud CLI: https://www.ibm.com/cloud/cli
# Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest
#
# Choose which platforms to deploy to using command line arguments:
# ./publish.sh AWS GCF IBM AZURE MEMORY
# Example to deploy to AWS and Azure: ./publish.sh 1 0 0 1 1024
#
# Get the function name from the config.json file.

cd "$(dirname "$0")"

# Get the function name from the config.json file.
function=`cat ./config.json | jq '.functionName' | tr -d '"'`

json=`cat config.json | jq -c '.test'`

echo
echo Deploying $function...
echo

# Deploy onto Local Kubernetes Cluster
echo
echo "----- Deploying onto Local Kubernetes Cluster -----"
echo

# Destroy and prepare build folder.
rm -rf build
mkdir build
mkdir build/$function

# Copy and position files in the build folder.
cp -R ../src/* ./build/$function
mv ./build/$function/handler.py ./build/$function/myFunction.py

cp -R ../platforms/openfaas/* ./build/$function
mv ./build/$function/hello.yml ./build/hello.yml
mv ./build/$function/.gitignore ./build/.gitignore

cd ./build

faas-cli up -f hello.yml --update=false --replace

cd ..

echo
echo Testing function on Local...
sleep 1
endPoint=`echo http://127.0.0.1:31112/function/hello`
curl -H "Content-Type: application/json" -X POST -d $json $endPoint
echo
