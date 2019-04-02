#!/bin/bash

# Mutli-platform Publisher. Used to publish FaaS Inspector Node.js functions onto AWS Lambda, Google Cloud Functions, IBM
# Cloud Functions, and Azure Functions.
#
# script requires packages:
# AWS CLI: apt install awscli 
# Google Cloud CLI: https://cloud.google.com/sdk/docs/quickstarts
# IBM Cloud CLI: https://www.ibm.com/cloud/cli
# Azure CLI: 
#
# To use this script, create files to provide your function name. Function must have the same name on ALL platforms.
# file: parfunction   The name of the function.


# Get the function name from the parfunction file.
filename="parfunction"
while read -r line
do
	parfunction=$line
done < "$filename"
cd ..

#
# Deploy onto AWS Lambda.
#
cd scr
zip -X -r ../index.zip *
cd ..
aws lambda update-function-code --function-name $parfunction --zip-file fileb://index.zip
rm index.zip

#
# Deploy onto Google Cloud Functions
#
cd scr
gcloud functions deploy $parfunction --runtime nodejs8 --trigger-http
cd ..

#
# Deploy onto IBM Cloud Functions
#
ibmcloud fn action update $parfunction

#
# Deploy onto Azure Functions
#