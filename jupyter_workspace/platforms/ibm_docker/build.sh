#!/bin/bash

location=$1
cd "$location" || exit

echo "Build: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')

echo "Build: Purging previous build..."
rm -rf ./.build
mkdir ./.build

echo "Build: Copying files..."
cp ../../../SAAF.py ./SAAF.py
cp -R ./* ./.build/

echo "Build: Cleaning up..."
rm ./.build/build.sh
rm ./.build/publish.sh
rm ./.build/run.sh
rm ./.build/config.json
rm ./.build/build.log
rm -rf ./.build/experiments || true

cd ./.build || exit

echo "Build: Building Docker Image..."
docker build -t ${function} .

echo "Build: Creating Zip..."
zip -X -r ./index.zip ./*