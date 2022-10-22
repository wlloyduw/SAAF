#!/bin/bash

location=$1
cd "$location" || exit

echo "Built!"
cp ../../../SAAF.py ./SAAF.py || true