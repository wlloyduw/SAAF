#!/bin/bash

location=$1
cd "$location" || exit

echo "1/4 Purging previous build..." >> ./build.log
rm -rf ./.build
mkdir ./.build

echo "2/4 Copying files..." >> ./build.log
cp ../../SAAF.py ./SAAF.py
cp -R ./* ./.build/

echo "3/4 Cleaning up..." >> ./build.log
rm ./.build/build.sh
rm ./.build/publish.sh
rm ./.build/run.sh
rm ./.build/config.json
rm ./.build/build.log
rm -rf ./.build/experiments || true

echo "4/4 Building Docker Image..." >> ./build.log
cd .build
docker build -t ${function} . >> ../build.log