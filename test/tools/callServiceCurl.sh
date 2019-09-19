#!/bin/bash

awsEndpoint=`cat config.json | jq '.awsEndpoint' | tr -d '"'`
googleEndpoint=`cat config.json | jq '.googleEndpoint' | tr -d '"'`
ibmEndpoint=`cat config.json | jq '.ibmEndpoint' | tr -d '"'`
azureEndpoint=`cat config.json | jq '.azureEndpoint' | tr -d '"'`
json=`cat config.json | jq -c '.payload'`

echo
echo ----- Testing $function on each platform with CURL. ------
echo

echo
echo Invoking $function on AWS Lambda...
echo
curl -H "Content-Type: application/json" -X POST -d $json $awsEndpoint

echo
echo Invoking $function on Google Cloud Functions...
echo
curl -H "Content-Type: application/json" -X POST -d $json $googleEndpoint

echo
echo Invoking $function on IBM Cloud Functions...
echo
curl -H "Content-Type: application/json" -X POST -d $json $ibmEndpoint

echo
echo Invoking $function on Azure Functions...
echo
curl -H "Content-Type: application/json" -X POST -d $json $azureEndpoint