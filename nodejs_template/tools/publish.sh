#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Node.js functions onto AWS Lambda, Google Cloud Functions, IBM
# Cloud Functions, and Azure Functions.
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
	mkdir build/node_modules
	
	# Copy files to build folder.
	cp -R ../src/* ./build
	cp -R ../platforms/aws/* ./build
	cp -R ../tools/node_modules/* ./build/node_modules
	
	# Zip and submit to AWS Lambda.
	cd ./build
	zip -X -r ./index.zip *
	aws lambda create-function --function-name $function --runtime nodejs10.x --role $lambdaRole --timeout 900 --handler index.handler --zip-file fileb://index.zip
	aws lambda update-function-code --function-name $function --zip-file fileb://index.zip
	aws lambda update-function-configuration --function-name $function --memory-size $memory --runtime nodejs10.x \
	--vpc-config SubnetIds=[$lambdaSubnets],SecurityGroupIds=[$lambdaSecurityGroups]
	cd ..

	echo Testing function on AWS Lambda...
	aws lambda invoke --invocation-type RequestResponse --cli-read-timeout 900 --function-name $function --region us-east-1 /dev/stdout


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
	mkdir build/node_modules
	
	# Copy files to build folder.
	cp -R ../src/* ./build
	cp -R ../platforms/ibm/* ./build
	cp -R ../tools/node_modules/* ./build/node_modules
	
	# Zip and submit to IBM Cloud Functions.
	cd ./build
	zip -X -r ./index.zip *
	ibmcloud fn action update $function --kind nodejs:8 --memory $memory index.zip
	cd ..

	echo Testing function on IBM Cloud Functions...
	ibmcloud fn action invoke --result $function
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
	mkdir build/node_modules
	mkdir build/$function
	
	# Copy and position files in the build folder.
	cp -R ../src/* ./build/$function
	mv ./build/$function/package.json ./build/package.json
	cp -R ../platforms/azure/* ./build
	mv ./build/index.js ./build/$function/index.js
	mv ./build/function.json ./build/$function/function.json
	cp -R ../tools/node_modules/* ./build/node_modules
	
	# Submit to Azure Functions
	cd ./build

	echo Creating resources...
	az group create --name $function --location eastus
	az storage account create --name $function --location eastus --resource-group $function --sku Standard_LRS
	az functionapp create --resource-group $function --consumption-plan-location eastus --name $function --runtime node --os-type Linux --output json --storage-account $function

	echo Deploying function...
	func azure functionapp publish $function --force
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
	mkdir build/node_modules
	
	# Copy files to build folder.
	cp -R ../src/* ./build
	cp -R ../platforms/google/* ./build
	cp -R ../tools/node_modules/* ./build/node_modules
	
	# Submit to Google Cloud Functions
	cd ./build
	gcloud functions deploy $function --source=. --runtime nodejs8 --entry-point helloWorld --timeout 540 --trigger-http --memory $memory
	cd ..

	echo Testing function on Google Cloud Functions...
	gcloud functions call $function
fi