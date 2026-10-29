#!/bin/bash

# Build the jar with Maven, copy it and the Dockerfile into .build/app, and zip them
# into .build/app.zip, the code artifact Lambda builds the MicroVM image from.

cd "$(dirname "$0")" || exit

echo "Build: Purging previous build..."
rm -rf ./.build
mkdir -p ./.build/app

echo "Build: Building jar with Maven..."
mvn -q clean package -f ../../pom.xml || exit 1

echo "Build: Copying files..."
cp ../../target/saaf-microvm.jar ./Dockerfile ./.build/app/

echo "Build: Creating zip..."
(cd ./.build/app && zip -X -q -r ../app.zip .)
