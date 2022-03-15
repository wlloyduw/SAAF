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
aws lambda create-function --function-name $function --role $role --timeout $timeout --code $code --package-type Image --memory-size $memory
aws lambda update-function-code --function-name $function --image-uri ${registryID}.dkr.ecr.${region}.amazonaws.com/saaf-functions:${function}
aws lambda update-function-configuration --function-name $function --memory-size $memory --vpc-config SubnetIds=[$subnets],SecurityGroupIds=[$security_groups]