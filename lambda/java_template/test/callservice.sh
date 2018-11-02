#!/bin/bash

# JSON object to pass to Lambda Function
json={"\"name\"":"\"Fred\u0020Smith\",\"param1\"":1,\"param2\"":2,\"param3\"":3}

echo "Invoking Lambda function using API Gateway"
time output=`curl -s -H "Content-Type: application/json" -X POST -d  $json {INSERT API GATEWAY URL HERE}`

echo ""
echo "CURL RESULT:"
echo $output
echo ""
echo ""

echo "Invoking Lambda function using AWS CLI"
time output=`aws lambda invoke --invocation-type RequestResponse --function-name {INSERT AWS FUNCTION NAME HERE} --region us-east-1 --payload $json /dev/stdout | head -n 1 | head -c -2 ; echo`
echo ""
echo "AWS CLI RESULT:"
echo $output
echo ""







