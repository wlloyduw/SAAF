#!/bin/bash

location=$1
cd "$location" || exit

json=$2

python3 local_runner.py "$json"