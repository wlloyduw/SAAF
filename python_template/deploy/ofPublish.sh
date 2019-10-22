#!/bin/bash

#
# This script allows functions to be deployed onto local kubernetes 
# clusters using OpenFaaS. It is still a work in progress.
# It is not recommended to be used yet. Functions must be named the same as your docker registry.
#
# Get the function name from the config.json file.

cd "$(dirname "$0")"

# Get the function name from the config.json file.
function=`cat ./config.json | jq '.functionName' | tr -d '"'`

json=`cat config.json | jq -c '.test'`

echo
echo Deploying $function...
echo

# Deploy onto Local Kubernetes Cluster
echo
echo "----- Deploying onto Local Kubernetes Cluster -----"
echo

# Destroy and prepare build folder.
rm -rf build
mkdir build
mkdir build/$function

# Copy and position files in the build folder.
cp -R ../src/* ./build/$function
mv ./build/$function/handler.py ./build/$function/myFunction.py

cp -R ../platforms/openfaas/* ./build/$function
mv ./build/$function/hello.yml ./build/$function.yml


sed "s/hello/$function/g" ./build/$function.yml > ./build/temp.yml
mv ./build/temp.yml ./build/$function.yml

mv ./build/$function/.gitignore ./build/.gitignore

cd ./build

faas-cli up -f $function.yml --update=false --replace

cd ..

echo WARNING! Function may not update immediately. Waiting 5 seconds...
sleep 1
echo 4..
sleep 1
echo 3..
sleep 1
echo 2..
sleep 1
echo 1..
sleep 1

echo
echo Testing function on Local...
endPoint=`echo http://127.0.0.1:31112/function/$function`
curl -H "Content-Type: application/json" -X POST -d $json $endPoint
echo
