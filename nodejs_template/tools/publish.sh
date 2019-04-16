#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Node.js functions onto AWS Lambda, Google Cloud Functions, IBM
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
# To use this script, create files to provide your function name. Function must have the same name on ALL platforms.
# file: parfunction   The name of the function.
#
# Choose which platforms to deploy to using command line arguments:
# ./publish.sh AWS GCF IBM AZURE MEMORY
# Example to deploy to AWS and Azure: ./publish.sh 1 0 0 1 1024
#
# WARNING for Azure: Azure Functions DOES NOT automatically download dependencies in the package.json file like IBM or Google. 
# You must manually install them to the ./tools directory and this script will automatically copy the node_modules folder and deploy it with your Azure function.


# Get the function name from the config.json file.
function=`cat ./config.json | jq '.functionName' | tr -d '"'`
functionApp=`cat ./config.json | jq '.azureFunctionApp' | tr -d '"'`
cd ..

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
	cd src
	cp ../platforms/aws/index.js index.js
	zip -X -r ./index.zip *
	aws lambda update-function-code --function-name $function --zip-file fileb://index.zip
	aws lambda update-function-configuration --function-name $function --memory-size $memory --runtime nodejs8.10
	rm index.zip
	rm index.js
	cd ..
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]
then
	echo
	echo "----- Deploying onto IBM Cloud Functions -----"
	echo
	cd src
	cp ../platforms/ibm/index.js index.js
	zip -X -r ./index.zip *
	ibmcloud fn action update $function --kind nodejs:8 --memory $memory index.zip
	rm index.js
	rm index.zip
	cd ..
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Azure Functions -----"
	echo
	cd src
	mkdir $function
	mv  -v ./* ./$function/
	mkdir node_modules
	mv ./$function/package.json package.json
	mv -v ../tools/node_modules/* ./node_modules/
	cp ../platforms/azure/function.json ./$function/function.json
	cp ../platforms/azure/host.json host.json
	cp ../platforms/azure/local.settings.json local.settings.json
	cp ../platforms/azure/index.js ./$function/index.js
	func azure functionapp publish $functionApp --force
	rm host.json
	rm local.settings.json
	rm ./$function/function.json
	rm ./$function/index.js
	mv  -v ./$function/* ./
	mv -v ./node_modules/* ../tools/node_modules/
	rmdir node_modules
	rmdir $function
	cd ..
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Google Cloud Functions -----"
	echo
	cd src
	cp ../platforms/google/index.js index.js
	gcloud functions deploy $function --source=. --runtime nodejs8 --trigger-http --memory $memory
	rm index.js
	cd ..
fi

cd tools