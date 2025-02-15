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
# Example to deploy to AWS and Azure: ./publish.sh 1 0 0 1 1024 {PATH TO CONFIG FILE}
#
# Get the function name from the config file.

cd "$(dirname "$0")"

# Load config.json if a value is not supplied.
config="./config.json"
if [[ ! -z $6 ]]; then
	config=$6
fi

# Get the function name from the config file.
function=$(cat $config | jq '.functionName' | tr -d '"')
json=$(cat $config | jq -c '.test')

#Define the memory value.
memory=$(cat $config | jq '.memorySetting' | tr -d '"')
if [[ ! -z $5 ]]; then
	memory=$5
fi

# Deploy onto AWS Lambda.
if [[ ! -z $1 && $1 -eq 1 ]]; then
	lambdaHandler=$(cat $config | jq '.lambdaHandler' | tr -d '"')
	lambdaRole=$(cat $config | jq '.lambdaRoleARN' | tr -d '"')
	lambdaSubnets=$(cat $config | jq '.lambdaSubnets' | tr -d '"')
	lambdaSecurityGroups=$(cat $config | jq '.lambdaSecurityGroups' | tr -d '"')
	lambdaEnvironment=$(cat $config | jq '.lambdaEnvironment' | tr -d '"')
	lambdaRuntime=$(cat $config | jq '.lambdaRuntime' | tr -d '"')

	echo Testing $function on AWS Lambda...
	aws lambda invoke --invocation-type RequestResponse --cli-read-timeout 900 --function-name $function --payload "$json" /dev/stdout
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]; then
	googleHandler=$(cat $config | jq '.googleHandler' | tr -d '"')
	googleRuntime=$(cat $config | jq '.googleRuntime' | tr -d '"')

	echo Testing $function on Google Cloud Functions... This may fail. It may take a moment for functions to start working after they are deployed.
	gcloud functions call $function --data $json
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]; then

	ibmRuntime=$(cat $config | jq '.ibmRuntime' | tr -d '"')
	ibmjson=$(cat $config | jq '.test' | tr -d '"' | tr -d '{' | tr -d '}' | tr -d ':')

	echo Testing $function on IBM Cloud Functions...
	ibmcloud fn action invoke $function -p $ibmjson --result
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]; then
	azureRuntime=$(cat $config | jq '.azureRuntime' | tr -d '"')

	echo Testing $function on Azure Functions...
	endPoint=$(func azure functionapp list-functions $function --show-keys | grep Invoke | head -n 1 | tr -d ' ' | cut -c11-)
	curl -H "Content-Type: application/json" -X POST -d $json $endPoint
	echo
fi
