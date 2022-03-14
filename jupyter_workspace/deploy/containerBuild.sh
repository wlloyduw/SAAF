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
handlerFile=$(cat $config | jq '.handlerFile' | tr -d '"')
json=$(cat $config | jq -c '.test')

echo
echo Deploying $function...
echo

#Define the memory value.
memory=$(cat $config | jq '.memorySetting' | tr -d '"')
if [[ ! -z $5 ]]; then
	memory=$5
fi

# Deploy onto AWS Lambda.
if [[ ! -z $1 && $1 -eq 1 ]]; then
	echo
	echo "----- Building for AWS Lambda -----"
	echo

	lambdaHandler=$(cat $config | jq '.lambdaHandler' | tr -d '"')
	lambdaRole=$(cat $config | jq '.lambdaRoleARN' | tr -d '"')
	lambdaSubnets=$(cat $config | jq '.lambdaSubnets' | tr -d '"')
	lambdaSecurityGroups=$(cat $config | jq '.lambdaSecurityGroups' | tr -d '"')
	lambdaEnvironment=$(cat $config | jq '.lambdaEnvironment' | tr -d '"')
	lambdaRuntime=$(cat $config | jq '.lambdaRuntime' | tr -d '"')

	echo "Cleaning previous build..." > ${function}_aws_build_progress.txt

	# Destroy and prepare build folder.
	rm -rf ${function}_aws_build
	mkdir ${function}_aws_build
	mkdir ${function}_aws_build/includes_${function}

	echo "Copying files..." >> ${function}_aws_build_progress.txt

	# Copy files to build folder.
	# cp -R ../src/* ./${function}_aws_build
	cp -R ../src/includes_${function}/* ./${function}_aws_build/includes_${function}
	cp ../src/handler_${function}.py ./${function}_aws_build/handler.py
	cp ../src/Inspector.py ./${function}_aws_build/Inspector.py

	cp -R ../platforms/aws/* ./${function}_aws_build
	cp -r ./package/* ./${function}_aws_build
	cp -r ./${function}_package/* ./${function}_aws_build

	# Check if custom docker file exists, and copy it to root of build folder/
	FILE=./${function}_aws_build/includes_${function}/Dockerfile
	if [ -f "$FILE" ]; then
		mv ./${function}_aws_build/includes_${function}/Dockerfile ./${function}_aws_build/Dockerfile
	fi

	echo "Building container..." >> ${function}_aws_build_progress.txt

	# Zip and submit to AWS Lambda.
	cd ./${function}_aws_build
	
	docker build -t ${function} . >> ../${function}_aws_build_progress.txt
	
	cd ..
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]; then
	echo
	echo "----- Deploying onto Google Cloud Functions -----"
	echo

	googleHandler=$(cat $config | jq '.googleHandler' | tr -d '"')
	googleRuntime=$(cat $config | jq '.googleRuntime' | tr -d '"')

	echo "GCF: Cleaning previous build..." > ${function}_gcf_build_progress.txt

	# Destroy and prepare build folder.
	rm -rf ${function}_gcf_build
	mkdir ${function}_gcf_build
	mkdir ${function}_gcf_build/includes_${function}

	echo "GCF: Copying files..." >> ${function}_gcf_build_progress.txt

	# Copy files to build folder.
	#cp -R ../src/* ./${function}_gcf_build
	cp -R ../src/includes_${function}/* ./${function}_gcf_build/includes_${function}
	cp ../src/handler_${function}.py ./${function}_gcf_build/handler.py
	cp ../src/Inspector.py ./${function}_gcf_build/Inspector.py

	cp -R ../platforms/google/* ./${function}_gcf_build
	cp ../platforms/google/main_gen2.py ./${function}_gcf_build/main.py
	cp -r ./package/* ./${function}_gcf_build/

	cd ./${function}_gcf_build

	echo "GCF: Building container with Buildpack" >> ../${function}_gcf_build_progress.txt

	pack build --builder gcr.io/buildpacks/builder:v1 --env GOOGLE_RUNTIME=python --env GOOGLE_FUNCTION_SIGNATURE_TYPE=http --env GOOGLE_FUNCTION_TARGET=$googleHandler ${function}
	#gcloud functions deploy $function --source=. --entry-point $googleHandler --runtime $googleRuntime --timeout 540 --trigger-http --memory $memory
	cd ..
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]; then
	echo
	echo "----- Deploying onto IBM Cloud Functions -----"
	echo

	ibmRuntime=$(cat $config | jq '.ibmRuntime' | tr -d '"')
	ibmjson=$(cat $config | jq '.test' | tr -d '"' | tr -d '{' | tr -d '}' | tr -d ':')

	echo "IBM: Cleaning previous build..." > ${function}_ibm_build_progress.txt

	# Destroy and prepare build folder.
	rm -rf ${function}_ibm_build
	mkdir ${function}_ibm_build
	mkdir ${function}_ibm_build/includes_${function}

	echo "IBM: Copying files..." >> ${function}_ibm_build_progress.txt

	# Copy files to build folder.
	#cp -R ../src/* ./${function}_ibm_build
	cp -R ../src/includes_${function}/* ./${function}_ibm_build/includes_${function}
	cp ../src/handler_${function}.py ./${function}_ibm_build/handler.py
	cp ../src/Inspector.py ./${function}_ibm_build/Inspector.py

	cp -R ../platforms/ibm/* ./${function}_ibm_build
	cp -r ./package/* ./${function}_ibm_build/

	# Check if custom docker file exists, and copy it to root of build folder/
	FILE=./${function}_ibm_build/includes_${function}/Dockerfile
	if [ -f "$FILE" ]; then
		mv ./${function}_ibm_build/includes_${function}/Dockerfile ./${function}_ibm_build/Dockerfile
	fi

	cd ./${function}_ibm_build
	echo "IBM: Building Docker container..." >> ../${function}_ibm_build_progress.txt

	docker build -t ${function} . >> ../${function}_ibm_build_progress.txt

	echo "IBM: Creating Function Zip..." >> ../${function}_ibm_build_progress.txt

	zip -X -r ./index.zip *

	cd ..
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]; then
	echo
	echo "----- Containers not supported on Azure -----"
	echo
fi
