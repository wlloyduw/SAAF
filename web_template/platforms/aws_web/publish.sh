#!/bin/bash

# Deploy the built package to an AWS Lambda Web Function.
#
# Requires the AWS CLI release that provides `aws lambda-web` and jq.
# Creates the function, a Home-Region endpoint, and an execution role when
# those resources do not already exist. Later runs publish a new revision
# to the same endpoint URL.
#
#   ./publish.sh
#   ./publish.sh /path/to/platforms/aws_web
#   DRY_RUN=1 ./publish.sh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
resolve_paths "${1:-}"

command -v jq >/dev/null 2>&1 || {
	echo "Publish: jq is required" >&2
	exit 1
}

if [[ ! -f "$CONFIG" ]]; then
	echo "Publish: config not found at $CONFIG" >&2
	exit 1
fi

function_name=$(jq -r '.function_name' "$CONFIG")
runtime=$(jq -r '.runtime // "nodejs24.x"' "$CONFIG")
timeout=$(jq -r '.timeout_seconds // 30' "$CONFIG")
region=$(jq -r '.region // "us-east-1"' "$CONFIG")
profile=$(jq -r '.profile // empty' "$CONFIG")
role=$(jq -r '.execution_role_arn // empty' "$CONFIG")
bucket=$(jq -r '.bucket_name // empty' "$CONFIG")
endpoint_name=$(jq -r '.endpoint_name // "dev"' "$CONFIG")
endpoint_type=$(jq -r '.endpoint_type // "HomeRegion"' "$CONFIG")
auth_type=$(jq -r '.auth_type // "ApplicationManaged"' "$CONFIG")
auto_mode=$(jq -r '.auto_deployment_mode // "LatestRevision"' "$CONFIG")
max_concurrency=$(jq -r '.max_concurrency_per_environment // empty' "$CONFIG")
max_environments=$(jq -r '.max_environments // empty' "$CONFIG")
rate_limit=$(jq -r '.rate_limit // empty' "$CONFIG")
description=$(jq -r '.description // empty' "$CONFIG")

if [[ ! "$function_name" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,62}[A-Za-z0-9]$ ]]; then
	echo "Publish: function_name must be 2-64 letters, numbers, hyphens, or underscores, and cannot start or end with a hyphen or underscore" >&2
	exit 1
fi

if [[ ! "$timeout" =~ ^[0-9]+$ ]] || [[ "$timeout" -lt 3 ]] || [[ "$timeout" -gt 900 ]]; then
	echo "Publish: timeout_seconds must be an integer from 3 to 900" >&2
	exit 1
fi

if [[ ! -f "$BUILD_DIR/index.js" ]]; then
	echo "Publish: building deployment directory..."
	"$SCRIPT_DIR/build.sh" "$LOCATION"
fi

args=(
	aws lambda-web deploy
	--name "$function_name"
	--code "$BUILD_DIR"
	--create
	--runtime "$runtime"
	--timeout-seconds "$timeout"
	--region "$region"
	--endpoint-name "$endpoint_name"
	--endpoint-type "$endpoint_type"
	--auth-type "$auth_type"
	--auto-deployment-mode "$auto_mode"
)

if [[ -n "$profile" ]]; then
	export AWS_PROFILE="$profile"
	args+=(--profile "$profile")
fi
if [[ -n "$role" ]]; then
	args+=(--execution-role-arn "$role")
fi
if [[ -n "$bucket" ]]; then
	args+=(--bucket-name "$bucket")
fi
if [[ -n "$max_concurrency" ]]; then
	args+=(--max-concurrency-per-environment "$max_concurrency")
fi
if [[ -n "$max_environments" ]]; then
	args+=(--max-environments "$max_environments")
fi
if [[ -n "$rate_limit" ]]; then
	args+=(--rate-limit "$rate_limit")
fi
if [[ -n "$description" ]]; then
	args+=(--description "$description")
fi

reserved='AWS_ACCESS_KEY|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SECRET_KEY|AWS_SECURITY_TOKEN|AWS_SESSION_TOKEN|AWS_DEFAULT_REGION|AWS_REGION|AWS_LAMBDA_HTTP_ENDPOINT|AWS_LAMBDA_RUNTIME_API|AWS_LAMBDA_INITIALIZATION_TYPE|AWS_LAMBDA_FUNCTION_MEMORY_SIZE|AWS_LAMBDA_METADATA_API|AWS_LAMBDA_METADATA_TOKEN'
while IFS= read -r pair; do
	[[ -z "$pair" ]] && continue
	key="${pair%%=*}"
	if [[ "$key" =~ ^($reserved)$ ]]; then
		echo "Publish: skipping reserved environment variable $key" >&2
		continue
	fi
	args+=(--env "$pair")
done < <(jq -r '.env // {} | to_entries[] | "\(.key)=\(.value|tostring)"' "$CONFIG")

if [[ "${DRY_RUN:-}" == "1" ]]; then
	printf 'DRY_RUN:'
	printf ' %q' "${args[@]}"
	printf '\n'
	exit 0
fi

command -v aws >/dev/null 2>&1 || {
	echo "Publish: AWS CLI is required" >&2
	exit 1
}
if ! aws lambda-web help >/dev/null 2>&1; then
	echo "Publish: this AWS CLI does not include lambda-web. Update the AWS CLI and rerun." >&2
	exit 1
fi

echo "Publish: Deploying $function_name to AWS Lambda Web Functions in $region..."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
"${args[@]}" | tee "$tmp"

url=$(grep -Eo 'https://[^[:space:]]*lambda-web[^[:space:]]*' "$tmp" | head -n 1 || true)
if [[ -z "$url" ]]; then
	echo "Publish: deploy finished but no endpoint URL was found in the output" >&2
	exit 1
fi

printf '%s\n' "$url" > "$ROOT/deploy/endpoint.url"
echo "Publish: Function deployed at $url"
