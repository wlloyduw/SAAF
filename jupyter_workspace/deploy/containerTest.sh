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

	echo Testing $function on Local Docker...
	docker run -d --name $function $function:latest
	results=$(docker exec $function curl -XPOST "http://localhost:8080/2015-03-31/functions/function/invocations" -d "$json")
	docker stop $function
	docker rm $function
	echo $results
fi

#docker run -d -v ~/.aws-lambda-rie:/aws-lambda -p 9100:8080 --entrypoint /aws-lambda/aws-lambda-rie $function:latest /entry.sh lambda_function.lambda_handler

#docker run -d -v ~/.aws-lambda-rie:/aws-lambda --name $function --entrypoint /aws-lambda/aws-lambda-rie $function:latest /usr/bin/python3 -m awslambdaric lambda_function.lambda_handler

#curl -XPOST "http://localhost:8080/2015-03-31/functions/function/invocations" -d '{"name": "Steve"}'