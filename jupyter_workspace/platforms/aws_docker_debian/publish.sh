#!/bin/bash

location=$1
cd "$location" || exit

echo "Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
memory=$(jq '.memory' < ./config.json | tr -d '"')
role=$(jq '.role' < ./config.json | tr -d '"')
subnets=$(jq '.subnets' < ./config.json | tr -d '"')
security_groups=$(jq '.security_groups' < ./config.json | tr -d '"')
timeout=$(jq '.timeout' < ./config.json | tr -d '"')
storage=$(jq '.storage' < ./config.json | tr -d '"')
profile=$(jq '.profile' < ./config.json | tr -d '"')
export AWS_PROFILE=$profile

cd ./.build || exit

echo "Creating AWS Registry..."
region=$(aws configure get region)
aws ecr create-repository --repository-name saaf-functions --image-scanning-configuration scanOnPush=true

echo "Pushing Docker Image..."
registryID=$(aws ecr describe-registry | jq '.registryId' | tr -d '"')
docker tag ${function}:latest ${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}
aws ecr get-login-password | docker login --username AWS --password-stdin ${registryID}.dkr.ecr.${region}.amazonaws.com
docker push ${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}
docker logout

echo "Deploying function..."
code={\"ImageUri\":\"${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}\"}

aws lambda get-function --function-name $function > /dev/null 2>&1
if [ 0 -eq $? ]; then
	echo "Publish: Updating function configuration..."
	aws lambda update-function-configuration \
		--function-name $function \
		--timeout $timeout \
		--memory-size $memory \
		--ephemeral-storage '{"Size": '$storage'}' \
		--vpc-config SubnetIds=[$subnets],SecurityGroupIds=[$security_groups]
	aws lambda wait function-updated --function-name "$function"

	echo "Publish: Updating function code..."
	aws lambda update-function-code \
		--function-name $function \
		--image-uri ${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}
	aws lambda wait function-updated --function-name "$function"
else
	echo "Publish: Creating new function..."
	aws lambda create-function \
		--function-name $function \
		--role $role \
		--timeout $timeout \
		--ephemeral-storage '{"Size": '$storage'}' \
		--code $code \
		--package-type Image \
		--memory-size $memory
	aws lambda wait function-exists --function-name "$function"
fi