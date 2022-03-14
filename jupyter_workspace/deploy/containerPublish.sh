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

	# Zip and submit to AWS Lambda.
	cd ./${function}_aws_build
	
	region=$(aws configure get region)
	aws ecr create-repository --repository-name saaf-functions --image-scanning-configuration scanOnPush=true
	registryID=$(aws ecr describe-registry | jq '.registryId' | tr -d '"')
	docker tag ${function}:latest ${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}
	aws ecr get-login-password | docker login --username AWS --password-stdin ${registryID}.dkr.ecr.${region}.amazonaws.com
	docker push ${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function} >> ../${function}_aws_build_progress.txt
	docker logout

	echo "Deploying to AWS Lambda..." >> ../${function}_aws_build_progress.txt

	code={\"ImageUri\":\"${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}\"}
	aws lambda create-function --function-name $function --role $lambdaRole --timeout 900 --code $code --package-type Image --memory-size $memory
	aws lambda update-function-code --function-name $function --image-uri ${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}
	aws lambda update-function-configuration --function-name $function --memory-size $memory --vpc-config SubnetIds=[$lambdaSubnets],SecurityGroupIds=[$lambdaSecurityGroups]

	cd ..
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]; then

	echo
	echo "----- Building for Google Cloud Functions -----"
	echo

	cd ./${function}_gcf_build
	region=$(gcloud info --format json | jq '.config.properties.compute.region' | tr -d '"')
	projectID=$(gcloud info --format json | jq '.config.project' | tr -d '"')
	gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin https://${region}-docker.pkg.dev
	docker tag ${function}:latest ${region}-docker.pkg.dev/${projectID}/gcf-artifacts/${function}
	docker push ${region}-docker.pkg.dev/${projectID}/gcf-artifacts/${function} >> ../${function}_gcf_build_progress.txt
	docker logout
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]; then

	dockerHubUsername=$(docker info | sed '/Username:/!d;s/.* //'); 

	cd ./${function}_ibm_build
	docker tag ${function}:latest ${dockerHubUsername}/saaf-functions:${function}
	docker push ${dockerHubUsername}/saaf-functions:${function} >> ../${function}_ibm_build_progress.txt

	echo "Deploying to IBM Cloud Functions..." >> ../${function}_ibm_build_progress.txt
	#ibmcloud fn action create ${function} --docker ${dockerHubUsername}/saaf-functions:${function} --web true  index.zip
	ibmcloud fn action update $function --docker ${dockerHubUsername}/saaf-functions:${function} --memory $memory index.zip

	cd ..
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]; then
	echo
	echo "----- Containers not supported on Azure -----"
	echo
fi
