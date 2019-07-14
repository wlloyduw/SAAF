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

lambdaRole=`cat ./config.json | jq '.lambdaRoleARN' | tr -d '"'`
lambdaSubnets=`cat ./config.json | jq '.lambdaSubnets' | tr -d '"'`
lambdaSecurityGroups=`cat ./config.json | jq '.lambdaSecurityGroups' | tr -d '"'`

functionApp=`cat ./config.json | jq '.azureFunctionApp' | tr -d '"'`

echo
echo Deploying $function...
echo

#Define the memory value.
memory=`cat ./config.json | jq '.memorySetting' | tr -d '"'`
if [[ ! -z $5 ]]
then
	memory=$5
fi

# Deploy onto AWS Lambda.
if [[ ! -z $1 && $1 -eq 1 ]]
then
	echo
	echo "----- Deploying onto AWS Lambda -----"
	echo

	# Destroy and prepare build folder.
	rm -rf build
	mkdir build

	# Copy files to build folder.
	cp -R ../src/* ./build
	cp -R ../platforms/aws/* ./build

	# Zip and submit to AWS Lambda.
	cd ./build
	zip -X -r ./index.zip *
	aws lambda create-function --function-name $function --runtime python3.7 --role $lambdaRole --timeout 900 --handler lambda_function.py --zip-file fileb://index.zip
	aws lambda update-function-code --function-name $function --zip-file fileb://index.zip
	aws lambda update-function-configuration --function-name $function --memory-size $memory --runtime python3.7 \
	--vpc-config SubnetIds=[$lambdaSubnets],SecurityGroupIds=[$lambdaSecurityGroups]
	cd ..
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]
then
	echo
	echo "----- Deploying onto IBM Cloud Functions -----"
	echo

	# Destroy and prepare build folder.
	rm -rf build
	mkdir build

	# Copy files to build folder.
	cp -R ../src/* ./build
	cp -R ../platforms/ibm/* ./build

	cd ./build
	zip -X -r ./index.zip *
	ibmcloud fn action update $function --kind python:3 --memory $memory index.zip
	cd ..
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Google Cloud Functions -----"
	echo

	# Destroy and prepare build folder.
	rm -rf build
	mkdir build

	# Copy files to build folder.
	cp -R ../src/* ./build
	cp -R ../platforms/google/* ./build

	cd ./build
	gcloud functions deploy $function --source=. --entry-point hello_world --runtime python37 --timeout 540 --trigger-http --memory $memory
	cd ..
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Azure Functions -----"
	echo

	# Destroy and prepare build folder.
	rm -rf build
	mkdir build
	mkdir build/$function

	# Copy and position files in the build folder.
	cp -R ../src/* ./build/$function

	
	cp -R ../platforms/azure/* ./build
	mv ./build/function.json ./build/$function/function.json
	mv ./build/__init__.py ./build/$function/__init__.py

	cd ./build
	python3.6 -m venv .env
	source .env/bin/activate
	func azure functionapp publish $functionApp --force
	deactivate
	cd ..
fi