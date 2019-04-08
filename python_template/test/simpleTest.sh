#!/bin/bash

# Simple test is meant to simply call each platform to verify that the publish script worked correctly.

function=`cat config.json | jq '.functionName' | tr -d '"'`
azureEndpoint=`cat config.json | jq '.azureEndpoint' | tr -d '"'`
json={"\"command\"":"\"env\""}

echo
echo ----- Testing $function on each platform ------
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

# IBM CAN'T SEND JSON THROUGH CLI. EDIT THIS IF YOU EDIT THE JSON. :(
ibmcloud fn action invoke $function -p command env --result

echo
echo Invoking $function on Azure Functions...
echo

#Azure CLI can't execute functions so you must define the azureEndpoint in config.json.
curl -H "Content-Type: application/json" -X POST -d  $json $azureEndpoint