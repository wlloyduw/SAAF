#!/bin/bash

# Build and deploy the Lambda Web Function from deploy/config.json.
# Usage, from this directory:
#   ./publish.sh

set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"
PLATFORM="$ROOT/platforms/aws_web"

"$PLATFORM/build.sh" "$PLATFORM"
"$PLATFORM/publish.sh" "$PLATFORM"
