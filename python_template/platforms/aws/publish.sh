#!/bin/bash

location=$1
cd "$location" || exit

echo "Publish: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
memory=$(jq '.memory' < ./config.json | tr -d '"')
handler=$(jq '.handler' < ./config.json | tr -d '"')
role=$(jq '.role' < ./config.json | tr -d '"')
subnets=$(jq '.subnets' < ./config.json | tr -d '"')
security_groups=$(jq '.security_groups' < ./config.json | tr -d '"')
env=$(jq '.env' < ./config.json | tr -d '"')
runtime=$(jq '.runtime' < ./config.json | tr -d '"')
storage=$(jq '.storage' < ./config.json | tr -d '"')
timeout=$(jq '.timeout' < ./config.json | tr -d '"')
profile=$(jq '.profile' < ./config.json | tr -d '"')
architectures=$(jq '.architectures' < ./config.json | tr -d '"')
export AWS_PROFILE=$profile

cd ./.build || exit

echo "Publish: Deploying function..."

aws lambda get-function --function-name $function > /dev/null 2>&1
if [ 0 -eq $? ]; then
	echo "Publish: Updating function configuration..."
	aws lambda update-function-configuration \
		--function-name "$function" \
		--runtime "$runtime" \
		--memory-size "$memory" \
		--role "$role" \
		--vpc-config SubnetIds=["$subnets"],SecurityGroupIds=["$security_groups"] \
		--environment "$env" \
		--timeout "$timeout" \
		--ephemeral-storage '{"Size": '$storage'}' \
		--handler "$handler"
	aws lambda wait function-updated --function-name "$function"

	echo "Publish: Updating function code..."
	aws lambda update-function-code --function-name "$function" --zip-file fileb://index.zip
	aws lambda wait function-updated --function-name "$function"
	aws lambda create-function-url-config --function-name "$function" --auth-type NONE
else
	echo "Publish: Creating new function..."
	aws lambda create-function \
		--function-name "$function" \
		--runtime "$runtime" \
		--memory-size "$memory" \
		--role "$role" \
		--vpc-config SubnetIds=["$subnets"],SecurityGroupIds=["$security_groups"] \
		--architectures "$architectures" \
		--environment "$env" \
		--timeout "$timeout" \
		--ephemeral-storage '{"Size": '$storage'}' \
		--handler "$handler" \
		--zip-file fileb://index.zip
	aws lambda wait function-exists --function-name "$function"
	aws lambda create-function-url-config --function-name "$function" --auth-type NONE
fi

echo "Publish: Function deployed!"
