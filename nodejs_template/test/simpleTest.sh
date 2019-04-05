#!/bin/bash

# Simple test is meant to simply call each platform to verify that the publish script worked correctly.

echo
echo ----- Testing $parfunction on each platform ------
echo


filename="parfunction"
while read -r line
do
	parfunction=$line
done < "$filename"

json={"\"name\"":"\"bob\",\"param1\"":1,\"param2\"":2,\"param3\"":3}

echo
echo Invoking $parfunction on AWS Lambda...
echo
aws lambda invoke --invocation-type RequestResponse --function-name $parfunction --region us-east-1 --payload $json /dev/stdout


echo
echo Invoking $parfunction on Google Cloud Functions...
echo
gcloud functions call $parfunction --data $json

echo
echo Invoking $parfunction on IBM Cloud Functions...
echo
ibmcloud fn action invoke $parfunction -p name bob --result

echo
echo Invoking $parfunction on Azure Functions...
echo