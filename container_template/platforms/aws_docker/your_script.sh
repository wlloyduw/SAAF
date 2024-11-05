#!/bin/bash

json_data=$1

name=$(echo "$json_data" | jq -r '.name')

echo "{\"message\": \"Hello $name!\"}"
