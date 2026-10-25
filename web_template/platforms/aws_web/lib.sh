#!/bin/bash

# Shared path and config lookup for the AWS Lambda Web platform scripts.
# Prefers a config.json next to the working location, then deploy/config.json.

resolve_paths() {
	SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
	ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
	if [[ -n "${1:-}" ]]; then
		LOCATION="$1"
	else
		LOCATION="$SCRIPT_DIR"
	fi

	if [[ -f "$LOCATION/config.json" ]]; then
		CONFIG="$LOCATION/config.json"
	elif [[ -f "$ROOT/deploy/config.json" ]]; then
		CONFIG="$ROOT/deploy/config.json"
	else
		CONFIG="$SCRIPT_DIR/default_config.json"
	fi

	BUILD_DIR="$LOCATION/.build"
}
