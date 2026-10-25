#!/bin/bash

# Assemble the Lambda Web deployment directory.
#
# The package root must contain index.js. This script copies the HTTP bridge
# and the platform-neutral source into .build/. aws lambda-web deploy uploads
# that directory. Pass the platform directory as $1, matching the Jupyter
# platform scripts. With no argument, the script directory is used.
#
#   ./build.sh
#   ./build.sh /path/to/platforms/aws_web

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
resolve_paths "${1:-}"

echo "Build: Purging previous build..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Build: Copying SAAF source and Lambda Web bridge..."
cp -R "$ROOT/src/." "$BUILD_DIR/"
cp "$SCRIPT_DIR/index.js" "$BUILD_DIR/index.js"
rm -f "$BUILD_DIR/.DS_Store"

if [[ ! -f "$BUILD_DIR/index.js" || ! -f "$BUILD_DIR/function.js" || ! -f "$BUILD_DIR/Inspector.js" ]]; then
	echo "Build: deployment directory is missing index.js, function.js, or Inspector.js" >&2
	exit 1
fi

echo "Build: Package ready at $BUILD_DIR"
