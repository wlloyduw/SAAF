#!/bin/bash

# Copy the function source, the server, and the Dockerfile into .build/app and zip
# them into .build/app.zip, the code artifact Lambda builds the MicroVM image from.

cd "$(dirname "$0")" || exit

echo "Build: Purging previous build..."
rm -rf ./.build
mkdir -p ./.build/app

echo "Build: Copying files..."
cp -R ../../src/. ./.build/app/
cp ./server.py ./Dockerfile ./.build/app/
find ./.build/app -name __pycache__ -prune -exec rm -rf {} +

echo "Build: Creating zip..."
(cd ./.build/app && zip -X -q -r ../app.zip .)
