#!/bin/bash
#
# SAAF
#
# @author Wes Lloyd
# @author Wen Shu
# @author Robert Cordingly
#
# Source this file once, then create a new Inspector for each invocation:
#
#   source ./Inspector.sh
#   Inspector
#   inspectAll
#   addAttribute "message" "Hello World!"
#   inspectAllDeltas
#   finish
#
# Requires bash 4.2 or newer and jq. Attributes are stored as JSON values and
# finish prints the JSON object containing all attributes collected.
#

#
# Use the jq binary included in the dependencies folder if it can run,
# otherwise use the jq installed on the system. Set SAAF_JQ to override.
#
SAAF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${SAAF_JQ:-}" ]; then
    if "$SAAF_DIR/dependencies/jq-linux64.dms" --version > /dev/null 2>&1; then
        SAAF_JQ="$SAAF_DIR/dependencies/jq-linux64.dms"
    else
        SAAF_JQ="jq"
    fi
fi

#
# Get the current time in ms and store it in SAAF_NOW.
#
__saaf_now() {
    if [ -n "${EPOCHREALTIME:-}" ]; then
        local microseconds=${EPOCHREALTIME/[.,]/}
        SAAF_NOW=$((10#$microseconds / 1000))
    else
        SAAF_NOW=$(date +%s%3N)
    fi
}

#
# Global variables that will persist through multiple invocations.
#
SAAF_INVOCATIONS=0
__saaf_now
SAAF_INITIALIZATION_TIME=$SAAF_NOW
SAAF_TICKS_PER_SECOND=$(getconf CLK_TCK 2> /dev/null || echo 100)

declare -gA __saaf_attributes=()
declare -ga __saaf_keys=()
declare -ga __saaf_cpu_polls=()

#
# Parse /proc/cpuinfo the same way as the other versions of SAAF.
#
__saaf_jq_cpu_info='
reduce (split("\n")[]) as $line ({coreInfo: {}, coreList: [], cpuCount: 0};
    ($line | split(":")) as $keyValue
    | ($keyValue[0] // "" | sub("^\\s+"; "") | sub("\\s+$"; "") | gsub(" "; "_")) as $key
    | if $key == "power_management" or $key == "CPU_revision" then
        .coreList += [.coreInfo] | .coreInfo = {}
    else
        (if $key == "processor" then .cpuCount += 1 else . end)
        | if ($keyValue | length) < 2 then .
        else
            ($keyValue[1] | sub("^\\s+"; "") | sub("\\s+$"; "")) as $value
            | .coreInfo[$key] = (if $key == "flags" or $key == "bugs" or $key == "Features"
                then $value | split(" ") else $value end)
        end
    end)
| (.coreList[0] // {}) as $first
| (.coreList[-1] // {}) as $last
| (if $first | has("model_name") then {cpuType: $first.model_name, cpuModel: $first.model, architecture: "x86"}
    elif $last | has("Model") then {cpuModel: $last.Model, architecture: "arm64"}
    else {architecture: "arm64"} end)
    + {cpuCores: .cpuCount, cpuInfo: .coreList}'

#
# Parse /proc/stat into a CPU poll with all CPU times converted from ticks into ms.
#
__saaf_jq_cpu_poll='
(1000 / $ticks) as $tickRate
| ["cpuUser", "cpuNice", "cpuKernel", "cpuIdle", "cpuIOWait",
    "cpuIrq", "cpuSoftIrq", "cpuSteal", "cpuGuest", "cpuGuestNice"] as $metrics
| split("\n") | .[0] |= sub("^cpu  "; "cpuTotal ")
| reduce .[] as $line ({time: $time};
    ($line | split(" ")) as $values
    | ($values[0] // "" | sub("^\\s+"; "") | sub("\\s+$"; "")) as $title
    | if $title | contains("cpu") then
        .[$title] = (reduce range(0; $metrics | length) as $i ({};
            .[$metrics[$i]] = (($values[$i + 1] // "0" | tonumber) * $tickRate)))
    elif ($values | length) >= 2 then
        .[$title] = ($values[1] | tonumber)
    else . end)'

#
# Calculate the CPU utilization of a function and recommend a memory setting.
#
__saaf_jq_recommend_configuration='
try (
    ((.functionMemory | tonumber) / 1792) as $availableCPUs
    | ((.cpuUserDelta + .cpuKernelDelta) / .userRuntime) as $utilizedCPUs
    | {availableCPUs: ($availableCPUs * 1000 | round / 1000),
        utilizedCPUs: ($utilizedCPUs * 1000 | round / 1000),
        recommendedMemory: ([[(if $availableCPUs - $utilizedCPUs < 0.1
            then 0.000556 * ($availableCPUs * 1.1) + 0.012346
            else 0.000556 * $utilizedCPUs + 0.012346 end | round), 128] | max, 10240] | min)}
) catch {SAAFRecommendConfigurationError: ("Unable to recommend a configuration. " + .)}'

#
# Encode a string as a JSON string and store it in SAAF_JSON.
#
__saaf_json_string() {
    local value=$1 backslash='\' quote='"'
    value=${value//"$backslash"/"$backslash$backslash"}
    value=${value//"$quote"/"$backslash$quote"}
    value=${value//$'\n'/"${backslash}n"}
    value=${value//$'\r'/"${backslash}r"}
    value=${value//$'\t'/"${backslash}t"}
    if [[ $value == *[[:cntrl:]]* ]]; then
        SAAF_JSON=$("$SAAF_JQ" -n --arg value "$1" '$value')
    else
        SAAF_JSON="\"$value\""
    fi
}

#
# Store a JSON value as an attribute, keeping the order attributes were added in.
#
__saaf_set() {
    if [ -z "${__saaf_attributes[$1]+x}" ]; then
        __saaf_keys+=("$1")
    fi
    __saaf_attributes[$1]=$2
}

#
# Store a string as an attribute.
#
__saaf_set_string() {
    __saaf_json_string "$2"
    __saaf_set "$1" "$SAAF_JSON"
}

#
# Store an environment variable as an attribute, or null if it is not set.
#
__saaf_set_env() {
    if [ -n "${!2+x}" ]; then
        __saaf_set_string "$1" "${!2}"
    else
        __saaf_set "$1" null
    fi
}

#
# Appended to a jq filter to print each key of the resulting object as "key<TAB>JSON value".
#
__saaf_jq_entries=' | to_entries[] | "\(.key)\t\(.value | tojson)"'

#
# Store each "key<TAB>JSON value" line read from standard input as an attribute.
#
__saaf_read_entries() {
    local key value
    while IFS=$'\t' read -r key value; do
        __saaf_set "$key" "$value"
    done
}

#
# Run a jq filter on JSON input and store every key of the resulting object as an attribute.
#
__saaf_set_entries() {
    __saaf_read_entries < <(printf '%s' "$1" | "$SAAF_JQ" -r "$2$__saaf_jq_entries")
}

#
# Initialize SAAF. Call this at the start of every invocation.
#
# startTime:            The time the function started running.
# invocations:          The number of times an Inspector has been created in this instance.
# initializationTime:   The time SAAF was first loaded by this instance.
#
Inspector() {
    SAAF_INVOCATIONS=$((SAAF_INVOCATIONS + 1))

    __saaf_attributes=()
    __saaf_keys=()
    __saaf_cpu_polls=()

    __saaf_now
    __saaf_start_time=$SAAF_NOW
    __saaf_set version 0.8
    __saaf_set lang '"bash"'
    __saaf_set startTime "$__saaf_start_time"
    __saaf_set invocations "$SAAF_INVOCATIONS"
    __saaf_set initializationTime "$SAAF_INITIALIZATION_TIME"

    __saaf_inspected_cpu=0
    __saaf_inspected_cpu_delta=0
    __saaf_inspected_memory=0
    __saaf_inspected_memory_delta=0
    __saaf_inspected_container=0
    __saaf_inspected_platform=0
    __saaf_inspected_linux=0
    __saaf_inspected_environment=0
}

#
# Collect information about the runtime container.
#
# uuid:            A unique identifier assigned to a container if one does not already exist.
# newcontainer:    Whether a container is new (no assigned uuid) or if it has been used before.
#
inspectContainer() {
    __saaf_inspected_container=1

    local myUuid=''
    local newContainer=1
    if [ -f /tmp/container-id ]; then
        IFS= read -r myUuid < /tmp/container-id || true
        newContainer=0
    else
        read -r myUuid < /proc/sys/kernel/random/uuid
        printf '%s' "$myUuid" > /tmp/container-id
    fi

    __saaf_set_string uuid "$myUuid"
    __saaf_set newcontainer "$newContainer"
}

#
# Collect information about the CPU assigned to this function.
#
# cpuType:         The model name of the CPU.
# cpuModel:        The model number of the CPU.
# architecture:    The architecture of the CPU (x86 or arm64).
# cpuCores:        The number of vCPUs allocated to the function.
# cpuInfo:         Detailed information about all aspects of the CPU.
#
inspectCPUInfo() {
    __saaf_read_entries < <("$SAAF_JQ" -r -R -s "$__saaf_jq_cpu_info$__saaf_jq_entries" /proc/cpuinfo)
}

#
# Collect timing CPU metrics. Each call records a poll of /proc/stat
# with all CPU times converted from ticks into milliseconds.
#
pollCPUStats() {
    __saaf_now
    __saaf_cpu_polls+=("$("$SAAF_JQ" -c -R -s --argjson time "$SAAF_NOW" \
        --argjson ticks "$SAAF_TICKS_PER_SECOND" "$__saaf_jq_cpu_poll" /proc/stat)")
}

#
# Collect information about the CPU assigned to this function.
#
# cpuUser:         Time spent normally executing in user mode.
# cpuNice:         Time spent executing niced processes in user mode.
# cpuKernel:       Time spent executing processes in kernel mode.
# cpuIdle:         Time spent idle.
# cpuIOWait:       Time spent waiting for I/O to complete.
# cpuIrq:          Time spent servicing interrupts.
# cpuSoftIrq:      Time spent servicing software interrupts.
# cpuSteal:        Time spent waiting for real CPU while hypervisor is using another virtual CPU.
# cpuGuest:        Time spent running a virtual CPU for guest operating systems.
# cpuGuestNice:    Time spent running a niced guest.
# bootTime:        Time when the host booted in seconds since the Unix epoch.
#
inspectCPU() {
    __saaf_inspected_cpu=1

    pollCPUStats

    __saaf_set_entries "${__saaf_cpu_polls[0]}" '.cpuTotal + {bootTime: .btime}'
}

#
# Compare information gained from inspectCPU to the current CPU metrics.
#
# Note: This function should be called at the end of your function and
# must be called AFTER inspectCPU.
#
# cpuUserDelta:        Time spent normally executing in user mode.
# cpuNiceDelta:        Time spent executing niced processes in user mode.
# cpuKernelDelta:      Time spent executing processes in kernel mode.
# cpuIdleDelta:        Time spent idle.
# cpuIOWaitDelta:      Time spent waiting for I/O to complete.
# cpuIrqDelta:         Time spent servicing interrupts.
# cpuSoftIrqDelta:     Time spent servicing software interrupts.
# cpuStealDelta:       Time spent waiting for real CPU while hypervisor is using another virtual CPU.
# cpuGuestDelta:       Time spent running a virtual CPU for guest operating systems.
# cpuGuestNiceDelta:   Time spent running a niced guest.
#
inspectCPUDelta() {
    if [ "$__saaf_inspected_cpu" = 1 ]; then
        __saaf_inspected_cpu_delta=1

        pollCPUStats
        local totalPolls=${#__saaf_cpu_polls[@]}

        __saaf_set_entries "[${__saaf_cpu_polls[0]},${__saaf_cpu_polls[$((totalPolls - 1))]}]" \
            '.[1].cpuTotal as $last | .[0].cpuTotal | with_entries(.value = $last[.key] - .value | .key += "Delta")'
    else
        __saaf_set_string SAAFCPUDeltaError "CPU not inspected before collecting deltas!"
    fi
}

#
# Make CPU polls accessible to the function.
#
processCPUPolls() {
    if [ ${#__saaf_cpu_polls[@]} -eq 0 ]; then
        __saaf_set cpuPolls '[]'
    else
        local IFS=,
        __saaf_set cpuPolls "[${__saaf_cpu_polls[*]}]"
    fi
}

#
# Inspects /proc/meminfo and /proc/vmstat. Add memory specific attributes:
#
# totalMemory:     Total memory allocated to the VM in kB.
# freeMemory:      Current free memory in kB when inspectMemory is called.
# pageFaults:      Total number of page faults experienced by the vm since boot.
# majorPageFaults: Total number of major page faults experienced since boot.
#
inspectMemory() {
    __saaf_inspected_memory=1

    local key value unit
    {
        read -r key value unit
        __saaf_set totalMemory "$value"
        read -r key value unit
        __saaf_set freeMemory "$value"
    } < /proc/meminfo

    if [ -f /proc/vmstat ]; then
        while read -r key value; do
            case $key in
                pgfault) __saaf_set pageFaults "$value" ;;
                pgmajfault) __saaf_set majorPageFaults "$value" ;;
            esac
        done < /proc/vmstat
    else
        __saaf_set_string SAAFMemoryError "/proc/vmstat does not exist!"
    fi
}

#
# Inspects /proc/vmstat to see how specific memory stats have changed.
#
# pageFaultsDelta:      The number of page faults experienced since inspectMemory was called.
# majorPageFaultsDelta: The number of major pafe faults since inspectMemory was called.
#
inspectMemoryDelta() {
    if [ "$__saaf_inspected_memory" = 1 ]; then
        __saaf_inspected_memory_delta=1
        if [ -f /proc/vmstat ]; then
            local key value
            while read -r key value; do
                case $key in
                    pgfault) __saaf_set pageFaultsDelta $((value - ${__saaf_attributes[pageFaults]:-0})) ;;
                    pgmajfault) __saaf_set majorPageFaultsDelta $((value - ${__saaf_attributes[majorPageFaults]:-0})) ;;
                esac
            done < /proc/vmstat
        else
            __saaf_set_string SAAFMemoryDeltaError "/proc/vmstat does not exist!"
        fi
    else
        __saaf_set_string SAAFMemoryDeltaError "Memory not inspected before collecting deltas!"
    fi
}

#
# Collect information about the current FaaS platform.
#
# platform:        The FaaS platform hosting this function.
# containerID:     A unique identifier for containers of a platform.
# vmID:            A unique identifier for virtual machines of a platform.
# functionName:    The name of the function.
# functionMemory:  The memory setting of the function.
# functionRegion:  The region the function is deployed onto.
#
inspectPlatform() {
    __saaf_inspected_platform=1

    if [ -n "${AWS_LAMBDA_LOG_STREAM_NAME+x}" ]; then
        __saaf_set_string platform "AWS Lambda"
        __saaf_set_env containerID AWS_LAMBDA_LOG_STREAM_NAME
        __saaf_set_env functionName AWS_LAMBDA_FUNCTION_NAME
        __saaf_set_env functionMemory AWS_LAMBDA_FUNCTION_MEMORY_SIZE
        __saaf_set_env functionRegion AWS_REGION

        local line cgroup=''
        while IFS= read -r line; do
            case $line in
                *2:cpu*) cgroup+=$line ;;
            esac
        done < /proc/self/cgroup
        __saaf_set_string vmID "${cgroup:20:6}"
    elif [ -n "${X_GOOGLE_FUNCTION_NAME+x}" ]; then
        __saaf_set_string platform "Google Cloud Functions"
        __saaf_set_env functionName X_GOOGLE_FUNCTION_NAME
        __saaf_set_env functionMemory X_GOOGLE_FUNCTION_MEMORY_MB
        __saaf_set_env functionRegion X_GOOGLE_FUNCTION_REGION
    elif [ -n "${__OW_ACTION_NAME+x}" ]; then
        __saaf_set_string platform "IBM Cloud Functions"
        __saaf_set_env functionName __OW_ACTION_NAME
        __saaf_set_env functionRegion __OW_API_HOST
        __saaf_set_string vmID "$(cat /sys/hypervisor/uuid 2> /dev/null || true)"
    elif [ -n "${CONTAINER_NAME+x}" ]; then
        __saaf_set_string platform "Azure Functions"
        __saaf_set_env containerID CONTAINER_NAME
        __saaf_set_env functionName WEBSITE_SITE_NAME
        __saaf_set_env functionRegion Location
    elif [ -n "${KUBERNETES_SERVICE_PORT_HTTPS+x}" ]; then
        __saaf_set_string platform "OpenFaaS EKS"
        __saaf_set_env http_host Http_Host
        __saaf_set_env http_foward Http_X_Forwarded_For
        __saaf_set_env http_start_time Http_X_Start_Time
        __saaf_set_env host_name HOSTNAME
    else
        __saaf_set_string platform "Unknown Platform"
    fi
}

#
# Estimate the CPU utilization of the function and recommend a memory setting.
# Requires inspectPlatform, inspectCPU, and inspectCPUDelta. Currently only
# supports AWS Lambda.
#
# availableCPUs:       The number of vCPUs available at the current memory setting.
# utilizedCPUs:        The number of vCPUs utilized while running user code.
# recommendedMemory:   The recommended memory setting for the function.
#
__saaf_recommend_configuration() {
    if [ "$__saaf_inspected_platform" = 1 ] && [ "$__saaf_inspected_cpu_delta" = 1 ]; then
        if [ "${__saaf_attributes[platform]}" = '"AWS Lambda"' ]; then
            local userRuntime=${__saaf_attributes[userRuntime]:-0}
            if [ "$userRuntime" = 0 ]; then
                __saaf_set_string SAAFRecommendConfigurationError "Unable to recommend a configuration. userRuntime must be greater than zero."
                return 0
            fi

            __saaf_set_entries "{\"functionMemory\": ${__saaf_attributes[functionMemory]},
                \"userRuntime\": $userRuntime,
                \"cpuUserDelta\": ${__saaf_attributes[cpuUserDelta]},
                \"cpuKernelDelta\": ${__saaf_attributes[cpuKernelDelta]}}" "$__saaf_jq_recommend_configuration"
        fi
    else
        __saaf_set_string SAAFRecommendConfigurationError "CPU, CPU Delta, and Platform must be inspected before recommending a configuration!"
    fi
}

#
# Collect information about the linux kernel.
#
# linuxVersion:    The version of the linux kernel.
#
inspectLinux() {
    __saaf_inspected_linux=1
    __saaf_set_string linuxVersion "$(uname -a)"
}

#
# Collect all environment variables. Each variable is added as an attribute
# using the variable's name as the key.
#
# Note: This is not called by inspectAll. Environment variables may contain
# secrets, such as the temporary AWS credentials provided by AWS Lambda.
#
inspectEnvironment() {
    __saaf_inspected_environment=1
    __saaf_set_entries "null" 'env'
}

#
# Run all data collection methods and record framework runtime.
#
inspectAll() {
    inspectContainer
    inspectCPUInfo
    inspectPlatform
    inspectLinux
    inspectMemory
    inspectCPU
    addTimeStamp "frameworkRuntime"
}

#
# Run all delta collection methods add userRuntime attribute to further isolate
# use code runtime from time spent collecting data.
#
inspectAllDeltas() {

    # Add the 'userRuntime' timestamp.
    if [ -n "${__saaf_attributes[frameworkRuntime]+x}" ]; then
        addTimeStamp "userRuntime" $((__saaf_start_time + ${__saaf_attributes[frameworkRuntime]}))
    fi

    __saaf_now
    local deltaTime=$SAAF_NOW
    inspectCPUDelta
    inspectMemoryDelta
    __saaf_recommend_configuration
    addTimeStamp "frameworkRuntimeDeltas" "$deltaTime"
}

#
# Add a custom attribute to the output. The value is stored as a string
# unless the third argument is "json", which stores the value as JSON.
#
# @param key A string to use as the key value.
# @param value The value to associate with that key.
# @param type Optional. Use "json" to add a number, boolean, list, or object.
#
addAttribute() {
    if [ "${3:-}" = "json" ]; then
        __saaf_set "$1" "$2"
    else
        __saaf_set_string "$1" "$2"
    fi
}

#
# Gets a custom attribute from the attribute list.
#
# @param key The key of the attribute.
# @return Prints the value of the attribute. Strings are printed without quotes.
#
getAttribute() {
    local value=${__saaf_attributes[$1]:-}
    if [[ $value == \"* ]]; then
        "$SAAF_JQ" -n -r --argjson value "$value" '$value'
    else
        printf '%s\n' "$value"
    fi
}

#
# Add custom time stamps to the output. The key value determines the name
# of the attribute and the value will be the time from Inspector initialization
# to this function call. Add timeSince to compare current time to a different time.
#
# @param key The name of the time stamp.
# @param timeSince Optional time in ms to compare the current time to.
#
addTimeStamp() {
    __saaf_now
    __saaf_set "$1" $((SAAF_NOW - ${2:-$__saaf_start_time}))
}

#
# Finalize the Inspector. Calculate the total runtime and print the JSON
# object containing all attributes collected.
#
# Note: Call finish directly rather than in a subshell, such as $(finish),
# so that the runtime and endTime attributes are recorded.
#
finish() {
    addTimeStamp 'runtime'
    __saaf_now
    __saaf_set endTime "$SAAF_NOW"

    local key json='' separator=''
    for key in "${__saaf_keys[@]}"; do
        __saaf_json_string "$key"
        json+="$separator$SAAF_JSON:${__saaf_attributes[$key]}"
        separator=','
    done
    printf '{%s}\n' "$json"
}
