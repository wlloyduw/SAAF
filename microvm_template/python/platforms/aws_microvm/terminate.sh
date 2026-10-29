#!/bin/bash

# Terminate every MicroVM running the image. Running MicroVMs are billed, and the idle
# policy in config.json only suspends them and terminates them later.

cd "$(dirname "$0")" || exit

function=$(jq -r '.function_name' < ./config.json)
export AWS_REGION=$(jq -r '.region' < ./config.json)

for microvm in $(aws lambda-microvms list-microvms --image-identifier "$function" --output text \
	--query "items[?state!='TERMINATING' && state!='TERMINATED'].microvmId"); do
	echo "Terminate: $microvm"
	aws lambda-microvms terminate-microvm --microvm-identifier "$microvm" > /dev/null
done
