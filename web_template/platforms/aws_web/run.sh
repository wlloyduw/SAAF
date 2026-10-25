#!/bin/bash

# Invoke a deployed Lambda Web Function and print the SAAF JSON body.
#
#   ./run.sh
#   ./run.sh /path/to/platforms/aws_web
#   ./run.sh /path/to/platforms/aws_web '{"name":"Ada"}'
#
# The endpoint is taken from ENDPOINT_URL, config endpoint_url, the URL saved
# by publish.sh, or aws lambda-web get-web-function-endpoint.

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
resolve_paths "${1:-}"

command -v jq >/dev/null 2>&1 || {
	echo "Run: jq is required" >&2
	exit 1
}
command -v curl >/dev/null 2>&1 || {
	echo "Run: curl is required" >&2
	exit 1
}

if [[ -n "${2:-}" ]]; then
	json=$2
else
	json=$(jq -c '.test' "$CONFIG")
fi

function_name=$(jq -r '.function_name' "$CONFIG")
region=$(jq -r '.region // "us-east-1"' "$CONFIG")
profile=$(jq -r '.profile // empty' "$CONFIG")
endpoint_name=$(jq -r '.endpoint_name // "dev"' "$CONFIG")
endpoint_url="${ENDPOINT_URL:-}"

if [[ -z "$endpoint_url" ]]; then
	endpoint_url=$(jq -r '.endpoint_url // empty' "$CONFIG")
fi
if [[ -z "$endpoint_url" && -f "$ROOT/deploy/endpoint.url" ]]; then
	endpoint_url=$(tr -d '[:space:]' < "$ROOT/deploy/endpoint.url")
fi
if [[ -z "$endpoint_url" ]]; then
	aws_args=(aws lambda-web get-web-function-endpoint --function-name "$function_name" --endpoint-name "$endpoint_name" --region "$region" --query domainName --output text)
	if [[ -n "$profile" ]]; then
		export AWS_PROFILE="$profile"
		aws_args+=(--profile "$profile")
	fi
	domain=$("${aws_args[@]}")
	endpoint_url="https://${domain}"
fi

body=$(mktemp)
trap 'rm -f "$body"' EXIT
code=$(curl -sS -o "$body" -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H 'Accept: application/json' --data "$json" "${endpoint_url%/}/")
cat "$body"
printf '\n'
if [[ "$code" != "200" ]]; then
	echo "Run: endpoint returned HTTP $code" >&2
	exit 1
fi
