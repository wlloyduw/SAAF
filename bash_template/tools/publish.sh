#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Bash functions onto AWS Lambda
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
lambdaRole=`cat ./config.json | jq '.lambdaRoleARN' | tr -d '"'`
lambdaSubnets=`cat ./config.json | jq '.lambdaSubnets' | tr -d '"'`
lambdaSecurityGroups=`cat ./config.json | jq '.lambdaSecurityGroups' | tr -d '"'`

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
	
    # Destroy and prepare build folder.
	rm -rf build
	mkdir build

    # Create folder with bootstrap and function...
    cp -R ../src/* ./build

    echo Assigning permissions...
    sudo chmod -R 755 ./build/*

	# Submit custom runtime to AWS Lambda.

    cd ./build
	zip -X -r ./function.zip *

	aws lambda create-function --function-name $function --runtime provided --role $lambdaRole --timeout 900 --handler function.handler --zip-file fileb://function.zip
	aws lambda update-function-code --function-name $function --zip-file fileb://function.zip
	aws lambda update-function-configuration --function-name $function --memory-size $memory --runtime provided \
	--vpc-config SubnetIds=[$lambdaSubnets],SecurityGroupIds=[$lambdaSecurityGroups]

	cd ..
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]
then
	echo
	echo "----- Deploying onto IBM Cloud Functions -----"
	echo
	echo "Bash FaaS Inspector does not support IBM Cloud Functions..."
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Azure Functions -----"
	echo
	echo "Bash FaaS Inspector does not support Azure Functions..."
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Google Cloud Functions -----"
	echo
	echo "Bash FaaS Inspector does not support Google Cloud Functions..."
fi