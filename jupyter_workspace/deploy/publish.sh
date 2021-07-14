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
	echo "----- Deploying onto AWS Lambda -----"
	echo

	lambdaHandler=$(cat $config | jq '.lambdaHandler' | tr -d '"')
	lambdaRole=$(cat $config | jq '.lambdaRoleARN' | tr -d '"')
	lambdaSubnets=$(cat $config | jq '.lambdaSubnets' | tr -d '"')
	lambdaSecurityGroups=$(cat $config | jq '.lambdaSecurityGroups' | tr -d '"')
	lambdaEnvironment=$(cat $config | jq '.lambdaEnvironment' | tr -d '"')
	lambdaRuntime=$(cat $config | jq '.lambdaRuntime' | tr -d '"')

	# Destroy and prepare build folder.
	rm -rf ${function}_aws_build
	mkdir ${function}_aws_build
	mkdir ${function}_aws_build/includes_${function}

	# Copy files to build folder.
	# cp -R ../src/* ./${function}_aws_build
	cp -R ../src/includes_${function}/* ./${function}_aws_build/includes_${function}/
	cp ../src/handler_${function}.py ./${function}_aws_build/handler.py
	cp ../src/Inspector.py ./${function}_aws_build/Inspector.py

	cp -R ../platforms/aws/* ./${function}_aws_build
	cp -r ./package/* ./${function}_aws_build
	cp -r ./${function}_package/* ./${function}_aws_build

	# Zip and submit to AWS Lambda.
	cd ./${function}_aws_build
	zip -X -r ./index.zip *
	aws lambda create-function --function-name $function --runtime $lambdaRuntime --role $lambdaRole --timeout 900 --handler $lambdaHandler --zip-file fileb://index.zip
	aws lambda update-function-code --function-name $function --zip-file fileb://index.zip
	aws lambda update-function-configuration --function-name $function --memory-size $memory --runtime $lambdaRuntime --vpc-config SubnetIds=[$lambdaSubnets],SecurityGroupIds=[$lambdaSecurityGroups] --environment "$lambdaEnvironment"
	cd ..

	echo
	echo Testing $function on AWS Lambda...
	aws lambda invoke --invocation-type RequestResponse --cli-read-timeout 900 --function-name $function --payload "$json" /dev/stdout
fi

# Deploy onto Google Cloud Functions
if [[ ! -z $2 && $2 -eq 1 ]]; then
	echo
	echo "----- Deploying onto Google Cloud Functions -----"
	echo

	googleHandler=$(cat $config | jq '.googleHandler' | tr -d '"')
	googleRuntime=$(cat $config | jq '.googleRuntime' | tr -d '"')

	# Destroy and prepare build folder.
	rm -rf ${function}_gcf_build
	mkdir ${function}_gcf_build
	mkdir ${function}_gcf_build/includes_${function}

	# Copy files to build folder.
	#cp -R ../src/* ./${function}_gcf_build
	cp -R ../src/includes_${function}/* ./${function}_gcf_build/includes_${function}
	cp ../src/handler_${function}.py ./${function}_gcf_build/handler.py
	cp ../src/Inspector.py ./${function}_gcf_build/Inspector.py

	cp -R ../platforms/google/* ./${function}_gcf_build
	cp -r ./package/* ./${function}_gcf_build/

	cd ./${function}_gcf_build
	gcloud functions deploy $function --source=. --entry-point $googleHandler --runtime $googleRuntime --timeout 540 --trigger-http --memory $memory
	cd ..

	echo
	echo Testing $function on Google Cloud Functions... This may fail. It may take a moment for functions to start working after they are deployed.
	gcloud functions call $function --data $json
fi

# Deploy onto IBM Cloud Functions
if [[ ! -z $3 && $3 -eq 1 ]]; then
	echo
	echo "----- Deploying onto IBM Cloud Functions -----"
	echo

	ibmRuntime=$(cat $config | jq '.ibmRuntime' | tr -d '"')
	ibmjson=$(cat $config | jq '.test' | tr -d '"' | tr -d '{' | tr -d '}' | tr -d ':')

	# Destroy and prepare build folder.
	rm -rf ${function}_ibm_build
	mkdir ${function}_ibm_build
	mkdir ${function}_ibm_build/includes_${function}

	# Copy files to build folder.
	#cp -R ../src/* ./${function}_ibm_build
	cp -R ../src/includes_${function}/* ./${function}_ibm_build/includes_${function}
	cp ../src/handler_${function}.py ./${function}_ibm_build/handler.py
	cp ../src/Inspector.py ./${function}_ibm_build/Inspector.py

	cp -R ../platforms/ibm/* ./${function}_ibm_build
	cp -r ./package/* ./${function}_ibm_build/

	cd ./${function}_ibm_build
	zip -X -r ./index.zip *
	ibmcloud fn action update $function --kind $ibmRuntime --memory $memory index.zip
	cd ..

	echo
	echo Testing function on IBM Cloud Functions...
	ibmcloud fn action invoke $function -p $ibmjson --result
fi

# Deploy onto Azure Functions
if [[ ! -z $4 && $4 -eq 1 ]]; then
	echo
	echo "----- Deploying onto Azure Functions -----"
	echo

	azureRuntime=$(cat $config | jq '.azureRuntime' | tr -d '"')

	# Destroy and prepare build folder.
	rm -rf ${function}_azure_build
	mkdir ${function}_azure_build
	mkdir ${function}_azure_build/includes_${function}
	mkdir ${function}_azure_build/$function

	# Copy and position files in the build folder.
	#cp -R ../src/* ./${function}_azure_build/$function
	cp -R ../src/includes_${function}/* ./${function}_azure_build/includes_${function}
	cp ../src/handler_${function}.py ./${function}_azure_build/handler.py
	cp ../src/Inspector.py ./${function}_azure_build/Inspector.py

	cp -R ../platforms/azure/* ./${function}_azure_build
	cp -r ./package/* ./${function}_azure_build/
	mv ./${function}_azure_build/function.json ./${function}_azure_build/$function/function.json
	mv ./${function}_azure_build/__init__.py ./${function}_azure_build/$function/__init__.py

	cd ./${function}_azure_build

	echo Creating resources...
	az group create --name $function --location eastus
	az storage account create --name $function --location eastus --resource-group $function --sku Standard_LRS
	az resource create -g $function -n $function --resource-type "Microsoft.Insights/components" --properties "{\"Application_Type\":\"web\"}"
	az functionapp create --resource-group $function --consumption-plan-location eastus --name $function --runtime $azureRuntime --os-type Linux --output json --storage-account $function --app-insights $function --functions-version 2

	echo Deploying function... This may fail if the function app is brand new. In that event, please run this script again.
	python3 -m venv .env
	source .env/bin/activate
	func azure functionapp publish $function --force
	deactivate
	cd ..

	echo
	echo Testing $function on Azure Functions...
	endPoint=$(func azure functionapp list-functions $function --show-keys | grep Invoke | head -n 1 | tr -d ' ' | cut -c11-)
	curl -H "Content-Type: application/json" -X POST -d $json $endPoint
	echo
fi
