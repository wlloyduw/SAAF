#!/bin/bash

# Copy the function source and the HTTP server into .build for aws lambda-web deploy.

cd "$(dirname "$0")" || exit

echo "Build: Purging previous build..."
rm -rf ./.build
mkdir ./.build

echo "Build: Copying files..."
cp -R ../../src/. ./.build/
cp ./index.js ./.build/
