#!/bin/bash

location=$1
cd "$location" || exit

echo "Build: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')

echo "Build: Purging previous build..."
rm -rf ./.build
mkdir ./.build
mkdir ./.build/$function

echo "Build: Copying files..."
cp ../../../SAAF.py ./SAAF.py
cp -R ./* ./.build/
mv ./.build/function.json ./.build/$function/function.json
mv ./.build/__init__.json ./.build/$function/__init__.json

echo "Build: Cleaning up..."
rm ./.build/build.sh
rm ./.build/publish.sh
rm ./.build/run.sh
rm ./.build/config.json
rm ./.build/build.log
rm -rf ./.build/experiments || true