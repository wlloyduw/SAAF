#!/bin/bash

# Build and deploy the Lambda function described in config.json, with a public function URL.
# The first publish creates the function. Later publishes update its code and configuration,
# waiting for each update to finish, since Lambda rejects a change while another is in progress.

cd "$(dirname "$0")" || exit
./build.sh || exit 1

echo "Publish: Loading config..."
function=$(jq -r '.function_name' < ./config.json)
memory=$(jq -r '.memory' < ./config.json)
storage=$(jq -r '.ephemeral_storage' < ./config.json)
architecture=$(jq -r '.architecture' < ./config.json)
runtime=$(jq -r '.runtime' < ./config.json)
timeout=$(jq -r '.timeout' < ./config.json)
role=$(jq -r '.role' < ./config.json)
environment=$(jq -c '{Variables: .env}' < ./config.json)
export AWS_REGION=$(jq -r '.region' < ./config.json)

if [[ -z $role ]]; then
	echo "Publish: Set role in config.json to the ARN of the function's execution role."
	exit 1
fi

if aws lambda get-function --function-name "$function" > /dev/null 2>&1; then
	echo "Publish: Updating function code..."
	aws lambda update-function-code --function-name "$function" --zip-file fileb://.build/function.zip \
		--architectures "$architecture" > /dev/null || exit 1
	aws lambda wait function-updated-v2 --function-name "$function" || exit 1

	echo "Publish: Updating function configuration..."
	aws lambda update-function-configuration --function-name "$function" --runtime "$runtime" --handler index.handler \
		--role "$role" --memory-size "$memory" --ephemeral-storage "Size=$storage" --timeout "$timeout" \
		--environment "$environment" > /dev/null || exit 1
	aws lambda wait function-updated-v2 --function-name "$function" || exit 1
else
	echo "Publish: Creating function..."
	aws lambda create-function --function-name "$function" --runtime "$runtime" --handler index.handler \
		--role "$role" --architectures "$architecture" --memory-size "$memory" --ephemeral-storage "Size=$storage" \
		--timeout "$timeout" --environment "$environment" --zip-file fileb://.build/function.zip > /dev/null || exit 1
	aws lambda wait function-active-v2 --function-name "$function" || exit 1
fi

# A function URL with no authentication, so HTTP clients such as FaaS Runner can call the function.
# A public function URL needs permission to call both lambda:InvokeFunctionUrl and lambda:InvokeFunction.
url=$(aws lambda get-function-url-config --function-name "$function" --query FunctionUrl --output text 2> /dev/null)
if [[ -z $url ]]; then
	echo "Publish: Creating function URL..."
	url=$(aws lambda create-function-url-config --function-name "$function" --auth-type NONE \
		--query FunctionUrl --output text) || exit 1
fi
policy=$(aws lambda get-policy --function-name "$function" --query Policy --output text 2> /dev/null)
if [[ $policy != *'"FunctionURLAllowPublicAccess"'* ]]; then
	aws lambda add-permission --function-name "$function" --statement-id FunctionURLAllowPublicAccess \
		--action lambda:InvokeFunctionUrl --principal '*' --function-url-auth-type NONE > /dev/null || exit 1
fi
if [[ $policy != *'"FunctionURLInvokeAllowPublicAccess"'* ]]; then
	aws lambda add-permission --function-name "$function" --statement-id FunctionURLInvokeAllowPublicAccess \
		--action lambda:InvokeFunction --principal '*' --invoked-via-function-url > /dev/null || exit 1
fi

echo "Publish: Function $function deployed at $url"
