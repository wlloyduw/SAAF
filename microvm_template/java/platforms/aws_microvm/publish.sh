#!/bin/bash

# Build the MicroVM image described in config.json and wait for Lambda to snapshot it.
# The first publish creates the image. Later publishes build a new image version, so
# MicroVMs still running an older version are terminated.

cd "$(dirname "$0")" || exit
./build.sh || exit 1

echo "Publish: Loading config..."
function=$(jq -r '.function_name' < ./config.json)
memory=$(jq -r '.memory' < ./config.json)
bucket=$(jq -r '.bucket' < ./config.json)
build_role=$(jq -r '.build_role' < ./config.json)
base_image=$(jq -r '.base_image' < ./config.json)
export AWS_REGION=$(jq -r '.region' < ./config.json)

if [[ -z $bucket || -z $build_role ]]; then
	echo "Publish: Set bucket and build_role in config.json. See the README for the build role policy."
	exit 1
fi

echo "Publish: Uploading code artifact..."
artifact="s3://$bucket/$function.zip"
aws s3 cp ./.build/app.zip "$artifact" || exit 1

# MicroVMs are not Lambda functions, so SAAF reads the image name, memory, and Region from these.
env=$(jq -c --arg region "$AWS_REGION" '.env + {SAAF_FUNCTION_NAME: .function_name,
	SAAF_FUNCTION_MEMORY: (.memory | tostring), SAAF_FUNCTION_REGION: $region}' < ./config.json)

# The server answers /ready during the build and /run when each MicroVM starts.
hooks='{"port":8080,
	"microvmHooks":{"run":"ENABLED","runTimeoutInSeconds":10,"resume":"DISABLED","resumeTimeoutInSeconds":10,
		"suspend":"DISABLED","suspendTimeoutInSeconds":10,"terminate":"DISABLED","terminateTimeoutInSeconds":10},
	"microvmImageHooks":{"ready":"ENABLED","readyTimeoutInSeconds":300,"validate":"DISABLED","validateTimeoutInSeconds":300}}'

args=(--code-artifact "uri=$artifact"
	--base-image-arn "arn:aws:lambda:$AWS_REGION:aws:microvm-image:$base_image"
	--build-role-arn "$build_role"
	--cpu-configurations architecture=ARM_64
	--resources "minimumMemoryInMiB=$memory"
	--hooks "$hooks"
	--environment-variables "$env")

echo "Publish: Building image..."
if aws lambda-microvms get-microvm-image --image-identifier "$function" > /dev/null 2>&1; then
	aws lambda-microvms update-microvm-image --image-identifier "$function" "${args[@]}" > /dev/null || exit 1
else
	aws lambda-microvms create-microvm-image --name "$function" "${args[@]}" > /dev/null || exit 1
fi

echo "Publish: Waiting for Lambda to build and snapshot the image..."
while true; do
	image=$(aws lambda-microvms get-microvm-image --image-identifier "$function") || exit 1
	state=$(jq -r '.state' <<< "$image")
	case $state in
		CREATED | UPDATED)
			break
			;;
		CREATE_FAILED | UPDATE_FAILED)
			echo "Publish: Build failed. $(jq -r '.stateReason // empty' <<< "$image")"
			echo "Publish: Build logs are in CloudWatch under /aws/lambda-microvms/$function"
			exit 1
			;;
	esac
	echo "Publish: Image is $state..."
	sleep 10
done
version=$(jq -r '.latestActiveImageVersion' <<< "$image")

echo "Publish: Terminating MicroVMs running older image versions..."
for microvm in $(aws lambda-microvms list-microvms --image-identifier "$function" --output text \
	--query "items[?imageVersion!='$version' && state!='TERMINATING' && state!='TERMINATED'].microvmId"); do
	aws lambda-microvms terminate-microvm --microvm-identifier "$microvm" > /dev/null
done

echo "Publish: Image $function version $version is ready!"
