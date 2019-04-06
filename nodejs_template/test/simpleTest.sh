#!/bin/bash

# Simple test is meant to simply call each platform to verify that the publish script worked correctly.

echo
echo ----- Testing $function on each platform ------
echo


function=`cat config.json | jq '.functionName' | tr -d '"'`

json={"\"command\"":"\"env\""}

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
ibmcloud fn action invoke $function -p command env --result

echo
echo Invoking $function on Azure Functions...
echo

#func azure function 