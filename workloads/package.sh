#!/bin/bash

# Stage workloads as deployable copies of their paradigm's template in .build/<deployment>/<workload>,
# and print the path of each stage's platform folder, which holds its publish.sh and run.sh.
#   ./package.sh calc_service web
#   ./package.sh all event-2048
#   ./package.sh all all
#
# Each deployment in config.json names a paradigm and the settings to deploy it with. A stage holds a
# src folder with the paradigm template's Inspector, the shared runner, and the workload, and the
# template's platform folder with a config.json built from the deployment's settings:
#   event     nodejs_template's Inspector and node_modules, with the handler and scripts in
#             platforms/aws_event from this folder.
#   web       web_template's Inspector and platforms/aws_web.
#   microvm   microvm_template/nodejs's Inspector and platforms/aws_microvm.

cd "$(dirname "$0")" || exit
root=$(cd .. && pwd)

usage() {
	echo "Usage: ./package.sh <workload|all> <deployment|all>" >&2
	echo "Deployments: $(jq -r '.deployments | keys_unsorted | join(", ")' < ./config.json)" >&2
	exit 1
}

if [[ $# -ne 2 ]]; then
	usage
fi

if [[ $1 == all ]]; then
	workloads=()
	for file in ./*/workload.json; do
		workloads+=("$(basename "$(dirname "$file")")")
	done
elif [[ -f ./$1/workload.json ]]; then
	workloads=("$1")
else
	echo "Package: $1 is not a workload. Each workload is a folder with a workload.json." >&2
	exit 1
fi

deployments=()
if [[ $2 == all ]]; then
	while IFS= read -r deployment; do
		deployments+=("$deployment")
	done < <(jq -r '.deployments | keys_unsorted[]' < ./config.json)
elif jq -e --arg deployment "$2" '.deployments[$deployment]' < ./config.json > /dev/null; then
	deployments=("$2")
else
	echo "Package: $2 is not a deployment in config.json." >&2
	usage
fi

prefix=$(jq -r '.prefix // "saaf"' < ./config.json) || exit 1

for deployment in "${deployments[@]}"; do
	paradigm=$(jq -r --arg deployment "$deployment" '.deployments[$deployment].paradigm' < ./config.json)
	case $paradigm in
		event)
			template=$root/nodejs_template
			platform=aws_event
			platform_source=./platforms/aws_event
			;;
		web)
			template=$root/web_template
			platform=aws_web
			platform_source=$template/platforms/aws_web
			;;
		microvm)
			template=$root/microvm_template/nodejs
			platform=aws_microvm
			platform_source=$template/platforms/aws_microvm
			;;
		*)
			echo "Package: Deployment $deployment has paradigm \"$paradigm\". It must be event, web, or microvm." >&2
			exit 1
			;;
	esac

	for workload in "${workloads[@]}"; do
		stage=./.build/$deployment/$workload
		rm -rf "$stage"
		mkdir -p "$stage/src" "$stage/platforms/$platform"

		# Files only, so build output and node_modules in the source folders are left out.
		# Later folders overwrite earlier ones, so shared/function.js replaces the template's.
		find "$template/src" ./shared "./$workload" -maxdepth 1 -type f ! -name '.*' -exec cp {} "$stage/src/" \;
		find "$platform_source" -maxdepth 1 -type f ! -name '.*' ! -name config.json \
			-exec cp {} "$stage/platforms/$platform/" \;
		if [[ $paradigm == event ]]; then
			mkdir -p "$stage/deploy"
			cp -R "$template/deploy/node_modules" "$stage/deploy/"
		fi

		# The platform's config.json, with the Region and the deployment's settings from config.json,
		# a function name for the workload, and the workload's defaults as the test payload.
		name="$prefix-$deployment-${workload//_/-}"
		jq --tab --slurpfile settings ./config.json --slurpfile workload "./$workload/workload.json" \
			--arg deployment "$deployment" --arg name "$name" \
			'. * {region: $settings[0].region} * ($settings[0].deployments[$deployment] | del(.paradigm))
				| .function_name = $name | .test = $workload[0].defaults' \
			"$platform_source/config.json" > "$stage/platforms/$platform/config.json" || exit 1

		echo "Package: Staged $workload for $deployment as $name" >&2
		echo "$PWD/${stage#./}/platforms/$platform"
	done
done
