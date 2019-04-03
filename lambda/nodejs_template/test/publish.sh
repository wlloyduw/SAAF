#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Node.js functions onto AWS Lambda, Google Cloud Functions, IBM
# Cloud Functions, and Azure Functions.
#
# Each platform's default handler is defined in the handlers folder. These are copied into the source folder as index.js
# and deployed onto each platform accordingly. Developers should write their function in the function.js file.
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
# ./publish.sh AWS GCF IBM AZURE
# Example to deploy to AWS and Azure: ./publish.sh 1 0 0 1
#


# Get the function name from the parfunction file.
filename="parfunction"
while read -r line
do
	parfunction=$line
done < "$filename"
cd ..


# Deploy onto AWS Lambda.
if [[ ! -z $1 && $1 -eq 1 ]]
then
	echo
	echo "----- Deploying onto AWS Lambda -----"
	echo
	cd scr
	cp ../handlers/aws.js index.js
	zip -X -r ./index.zip *
	aws lambda update-function-code --function-name $parfunction --zip-file fileb://index.zip
	rm index.zip
	rm index.js
	cd ..
fi


# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Google Cloud Functions -----"
	echo
	cd scr
	cp ../handlers/google.js index.js
	gcloud functions deploy $parfunction --source=. --runtime nodejs8 --trigger-http
	rm index.js
	cd ..
fi


# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]
then
	echo
	echo "----- Deploying onto IBM Cloud Functions -----"
	echo
	cd scr
	cp ../handlers/ibm.js index.js
	cat Inspector.js >> index.js
	cat function.js >> index.js
	ibmcloud fn action update $parfunction index.js
	rm index.js
	cd ..
fi


# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]
then
	echo
	echo "----- Deploying onto Azure Functions -----"
	echo
	cd scr
	cp ../handlers/azure.js ./index.js

	rm index.js
	cd ..
fi