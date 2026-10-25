#!/bin/bash

# Start the Lambda Web HTTP server on this machine.
# Listens on localhost:3000 unless AWS_LAMBDA_HTTP_ENDPOINT is already set.
#   ./local.sh

set -euo pipefail

cd "$(dirname "$0")/.."
export AWS_LAMBDA_HTTP_ENDPOINT="${AWS_LAMBDA_HTTP_ENDPOINT:-localhost:3000}"
exec node platforms/aws_web/index.js
