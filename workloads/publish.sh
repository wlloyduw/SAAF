#!/bin/bash

# Package workloads, deploy each one with its platform's publish.sh, and tag it with tag.sh.
#   ./publish.sh calc_service event-2048
#   ./publish.sh all web
#   ./publish.sh all all

cd "$(dirname "$0")" || exit
output=$(./package.sh "$@") || exit 1

# The AWS CLI profile from config.json, when it names one, so every deploy goes to the same account.
profile=$(jq -r '.profile // empty' < ./config.json)
if [[ -n $profile ]]; then
	export AWS_PROFILE=$profile
fi

platforms=()
while IFS= read -r platform; do
	platforms+=("$platform")
done <<< "$output"

failed=()
for platform in "${platforms[@]}"; do
	# .build/<deployment>/<workload>/platforms/aws_<paradigm> is labeled <deployment>/<workload>.
	label=${platform#"$PWD"/.build/}
	label=${label%/platforms/*}
	echo
	echo "----- Publishing $label -----"
	if ! "$platform/publish.sh"; then
		failed+=("$label")
	# Tags attribute the deployment's costs in AWS billing. See tag.sh.
	elif ! ./tag.sh "${label#*/}" "${label%%/*}"; then
		failed+=("$label (tags)")
	fi
done

echo
if [[ ${#failed[@]} -gt 0 ]]; then
	echo "Publish: ${#failed[@]} of ${#platforms[@]} failed: ${failed[*]}"
	exit 1
fi
echo "Publish: All ${#platforms[@]} published."
