#!/bin/bash

# Copy the function source, the handler, and nodejs_template's node_modules into .build/function
# and zip them into .build/function.zip, the deployment package for aws lambda.

cd "$(dirname "$0")" || exit

echo "Build: Purging previous build..."
rm -rf ./.build
mkdir -p ./.build/function

echo "Build: Copying files..."
cp -R ../../src/. ./.build/function/
cp ./index.js ./.build/function/
# nodejs_template's Inspector loads the uuid package from deploy/node_modules.
cp -R ../../deploy/node_modules ./.build/function/

echo "Build: Creating zip..."
(cd ./.build/function && zip -X -q -r ../function.zip .)
