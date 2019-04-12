#!/bin/bash
function=`cat config.json | jq '.functionName' | tr -d '"'`
json=`cat config.json | jq -c '.payload'`
ibmjson=`cat config.json | jq '.payload' | tr -d '"' | tr -d '{' | tr -d '}' | tr -d ':'`

echo
echo ----- Testing $function on each platform with CLI. ------
echo

echo
echo Invoking $function on AWS Lambda...
echo
aws lambda invoke --invocation-type RequestResponse --function-name $function --region us-east-1 --payload $json /dev/stdout

echo
echo Invoking $function on Google Cloud Functions...
echo
gcloud functions call $function --data $json

echo
echo Invoking $function on IBM Cloud Functions...
echo
ibmcloud fn action invoke $function -p $ibmjson --result

# NOTE: The Azure CLI does not have a method to invoke functions. CURL must be used to test Azure Functions.