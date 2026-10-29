#!/bin/bash

# Run a workload on this machine without SAAF, to check its results and runtime before deploying.
# SAAF reads /proc, so it only runs on Linux, but a workload runs anywhere Node.js 24 does.
#   ./local.sh calc_service
#   ./local.sh calc_service '{"threads":2}'

cd "$(dirname "$0")" || exit

if [[ $# -lt 1 || ! -f ./$1/workload.json ]]; then
	echo "Usage: ./local.sh <workload> [json]" >&2
	exit 1
fi

json='{}'
if [[ -n $2 ]]; then
	json=$2
fi

stage=./.build/local/$1
rm -rf "$stage"
mkdir -p "$stage"
find ./shared "./$1" -maxdepth 1 -type f ! -name '.*' -exec cp {} "$stage/" \;

node -e 'require(process.argv[1]).run(JSON.parse(process.argv[2])).then((result) => console.log(JSON.stringify(result, null, 2)))' \
	"$PWD/${stage#./}/runner.js" "$json"
