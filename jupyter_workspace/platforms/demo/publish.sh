#!/bin/bash

location=$1
cd "$location" || exit

cd ./.build || exit

echo "Publish: Deploying function..."

cat handler.py | base64 -w 0 > code.txt

echo "Publish: Function deployed!"
