#!/bin/bash

location=$1
cd "$location" || exit

function=$(jq '.function_name' < ./config.json | tr -d '"')
gateway=$(jq '.gateway' < ./config.json | tr -d '"')
image_repo=$(jq '.image_repo' < ./config.json | tr -d '"')

echo "Build: Purging previous build..."
rm -rf ./.build/
mkdir ./.build
mkdir ./.build/$function

echo "Build: Copying files..."
cp ../../SAAF.py ./SAAF.py
cp -R ./* ./.build/$function

echo "Build: Swapping some files around..."
mv ./.build/$function/handler.py ./.build/$function/your_function.py 
mv ./.build/$function/open_faas_handler.py ./.build/$function/handler.py 
mv ./.build/$function/default.yml ./.build/$function.yml

echo "Build: Creating yaml file..."

echo "version: 1.0" > ./.build/$function.yml
echo "provider:" >> ./.build/$function.yml
echo "  name: openfaas" >> ./.build/$function.yml
echo "  gateway: $gateway" >> ./.build/$function.yml
echo "functions:" >> ./.build/$function.yml
echo "  $function:" >> ./.build/$function.yml
echo "    lang: python3-debian" >> ./.build/$function.yml
echo "    handler: ./$function" >> ./.build/$function.yml
echo "    image: $image_repo:$function" >> ./.build/$function.yml

echo "Build: Cleaning up..."
rm ./.build/$function/build.sh
rm ./.build/$function/publish.sh
rm ./.build/$function/setup.sh
rm ./.build/$function/run.sh
rm ./.build/$function/config.json
rm ./.build/$function/build.log
rm -rf ./.build/$function/experiments || true
