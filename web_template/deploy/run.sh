#!/bin/bash

# POST the test payload, or a JSON argument, to the deployed endpoint.
# Usage, from this directory:
#   ./run.sh
#   ./run.sh '{"name":"Ada"}'

set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"
PLATFORM="$ROOT/platforms/aws_web"

if [[ -n "${1:-}" ]]; then
	exec "$PLATFORM/run.sh" "$PLATFORM" "$1"
fi
exec "$PLATFORM/run.sh" "$PLATFORM"
