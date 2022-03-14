#!/bin/bash

location=$1
cd "$location" || exit

python3 local_runner.py