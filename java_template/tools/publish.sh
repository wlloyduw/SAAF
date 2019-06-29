#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Java functions onto AWS Lambda
#
# Each platform's default function is defined in the platforms folder. These are copied into the source folder as index.js
# and deployed onto each platform accordingly. Developers should write their function in the function.js file. 
# All source files should be in the src folder and dependencies defined in package.json. 
# Node Modules must be installed in tools/node_modules. This folder will be deployed with your function.
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

function=`cat ./config.json | jq '.functionName' | tr -d '"'`
functionApp=`cat ./config.json | jq '.azureFunctionApp' | tr -d '"'`
lambdaRole=`cat ./config.json | jq '.lambdaRoleARN' | tr -d '"'`

echo
echo Deploying $function....
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
	
	echo "Building jar with Maven..."
	mvn clean -f "../pom.xml"
	mvn verify -f "../pom.xml"
	
	# Submit jar to AWS Lambda.
	cd ..
	cd target
	aws lambda create-function --function-name $function --runtime java8 --role $lambdaRole --timeout 900 --handler lambda.Hello::handleRequest --zip-file fileb://lambda_test-1.0-SNAPSHOT.jar
	aws lambda update-function-code --function-name $function --zip-file fileb://lambda_test-1.0-SNAPSHOT.jar
	aws lambda update-function-configuration --function-name $function --memory-size $memory --runtime java8
	cd ..
	cd tools
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]
then
	echo
	echo "----- Deploying onto IBM Cloud Functions -----"
	echo
	echo "Java FaaS Inspector does not support IBM Cloud Functions..."
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Azure Functions -----"
	echo
	echo "Java FaaS Inspector does not support AzureFunctions..."
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Google Cloud Functions -----"
	echo
	echo "Java FaaS Inspector does not support Google Cloud Functions..."
fi