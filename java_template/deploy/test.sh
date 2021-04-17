#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Java functions onto AWS Lambda
# @author Robert Cordingly
#
# Each platform's default function is defined in the platforms folder. These are copied into the source folder
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
# Example to deploy to AWS and Azure: ./publish.sh 1 0 0 1 1024 {OPTIONAL PATH TO CSV}
#
# Get the function name from the config.json file.

cd "$(dirname "$0")"

# Load config.json if a value is not supplied.
config="./config.json"
if [[ ! -z $6 ]]; then
	config=$6
fi

# Get function name from config.
function=$(cat $config | jq '.functionName' | tr -d '"')

#Define the memory value.
memory=$(cat ./config.json | jq '.memorySetting' | tr -d '"')
if [[ ! -z $5 ]]; then
	memory=$5
fi

# Deploy onto AWS Lambda.
if [[ ! -z $1 && $1 -eq 1 ]]; then
	echo
	echo "----- Testing on AWS Lambda -----"
	echo

	# Get lambda variables.
	lambdaHandler=$(cat $config | jq '.lambdaHandler' | tr -d '"')
	lambdaRole=$(cat $config | jq '.lambdaRoleARN' | tr -d '"')
	lambdaSubnets=$(cat $config | jq '.lambdaSubnets' | tr -d '"')
	lambdaSecurityGroups=$(cat $config | jq '.lambdaSecurityGroups' | tr -d '"')
	lambdaEnvironment=$(cat $config | jq '.lambdaEnvironment' | tr -d '"')
	lambdaRuntime=$(cat $config | jq '.lambdaRuntime' | tr -d '"')
	json=$(cat $config | jq -c -a '.test')

	echo
	echo Testing function on AWS Lambda...
	aws lambda invoke --invocation-type RequestResponse --cli-read-timeout 900 --function-name $function --payload "$json" /dev/stdout
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]; then
	echo
	echo "----- Testing on IBM Cloud Functions -----"
	echo

	echo
	echo Testing function on IBM Cloud Functions...
	ibmcloud fn action invoke $function -p $ibmjson --result

fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]; then
	echo
	echo "----- Testing on Azure Functions -----"
	echo
	echo "Java SAAF does not support Azure Functions..."
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]; then
	echo
	echo "----- Testing on Google Cloud Functions -----"
	echo
	echo "Java SAAF does not support Google Cloud Functions..."
fi
