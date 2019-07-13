#!/bin/bash

#
# FaaS Inspector Bash Version
#
# @author Wes Lloyd
# @author Robert Cordingly
#

# Version variables.
version=0.1
lang="bash"
startTime=( $(($(date +%s%N)/1000000)) )

# Generate UUID, check if container exists, stamp container.
uuid=0
newContainer=0
if [ ! -f /tmp/container-id ]; then
    #uuid=$(./dependencies/uuid)
    echo "$uuid" >> /tmp/container-id
    newContainer=1
else
    uuid=$(cat /tmp/container-id)
fi
vmuptime=$(grep 'btime' /proc/stat | cut -c 7-)
contextSwitches=$(grep 'ctxt' /proc/stat | cut -c 6-)

# Get CPU Metrics
IFS=' ' read -r -a CPUMetrics <<< "$(cat /proc/stat | grep "^cpu" | head -1)"
cpuUsr=${CPUMetrics[1]}
cpuNice=${CPUMetrics[2]}
cpuKrn=${CPUMetrics[3]}
cpuIdle=${CPUMetrics[4]}
cpuIowait=${CPUMetrics[5]}
cpuIrq=${CPUMetrics[6]}
cpuSoftIrq=${CPUMetrics[7]}
vmcpusteal=${CPUMetrics[8]}

# Get CPU Information
cpuModel=$(grep 'model' /proc/cpuinfo | head -1 | cut -c 10-)
cpuType=$(grep 'model name' /proc/cpuinfo | head -1 | cut -c 14-)

# Get Lambda VM ID
vmID=$(cat /proc/self/cgroup | grep '2:cpu' | head -1 | cut -c 21- | head -c 6)

# Get framework runtime.
frameworkRuntime=$(($(($(date +%s%N)/1000000))-startTime))


#
# USER CODE GOES HERE
#

# Finalize runtime and calculate deltas.
runtime=$(($(($(date +%s%N)/1000000))-startTime))
IFS=' ' read -r -a CPUMetrics <<< "$(cat /proc/stat | grep "^cpu" | head -1)"
cpuUsrDelta=$((CPUMetrics[1]-cpuUsr))
cpuNiceDelta=$((CPUMetrics[2]-cpuNice))
cpuKrnDelta=$((CPUMetrics[3]-cpuKrn))
cpuIdleDelta=$((CPUMetrics[4]-cpuIdle))
cpuIowaitDelta=$((CPUMetrics[5]-cpuIowait))
cpuIrqDelta=$((CPUMetrics[6]-cpuIrq))
cpuSoftIrqDelta=$((CPUMetrics[7]-cpuSoftIrq))
vmcpustealDelta=$((CPUMetrics[8]-vmcpusteal))

# Build Json response.
jsonString=$( ./dependencies/jq-linux64.dms -n \
            --arg version "$version" \
            --arg lang "$lang" \
            --arg uuid "$uuid" \
            --arg newcontainer "$newContainer" \
            --arg vmuptime "$vmuptime" \
            --arg contextSwitches "$contextSwitches" \
            --arg cpuUsr "$cpuUsr" \
            --arg cpuNice "$cpuNice" \
            --arg cpuKrn "$cpuKrn" \
            --arg cpuIdle "$cpuIdle" \
            --arg cpuIowait "$cpuIowait" \
            --arg cpuIrq "$cpuIrq" \
            --arg cpuSoftIrq "$cpuSoftIrq" \
            --arg vmcpusteal "$vmcpusteal" \
            --arg cpuUsrDelta "$cpuUsrDelta" \
            --arg cpuNiceDelta "$cpuNiceDelta" \
            --arg cpuKrnDelta "$cpuKrnDelta" \
            --arg cpuIdleDelta "$cpuIdleDelta" \
            --arg cpuIowaitDelta "$cpuIowaitDelta" \
            --arg cpuIrqDelta "$cpuIrqDelta" \
            --arg cpuSoftIrqDelta "$cpuSoftIrqDelta" \
            --arg vmcpustealDelta "$vmcpustealDelta" \
            --arg cpuModel "$cpuModel" \
            --arg cpuType "$cpuType" \
            --arg runtime "$runtime" \
            --arg frameworkRuntime "$frameworkRuntime" \
            --arg vmID "$vmID" \
            '{version: $version,
            lang: $lang,
            uuid: $uuid,
            newcontainer: $newcontainer,
            vmuptime: $vmuptime,
            contextSwitches: $contextSwitches,
            cpuUsr: $cpuUsr,
            cpuNice: $cpuNice,
            cpuKrn: $cpuKrn,
            cpuIdle: $cpuIdle,
            cpuIowait: $cpuIowait,
            cpuIrq: $cpuIrq,
            cpuSoftIrq: $cpuSoftIrq,
            vmcpusteal: $vmcpusteal,
            cpuUsrDelta: $cpuUsrDelta,
            cpuNiceDelta: $cpuNiceDelta,
            cpuKrnDelta: $cpuKrnDelta,
            cpuIdleDelta: $cpuIdleDelta,
            cpuIowaitDelta: $cpuIowaitDelta,
            cpuIrqDelta: $cpuIrqDelta,
            cpuSoftIrqDelta: $cpuSoftIrqDelta,
            vmcpustealDelta: $vmcpustealDelta,
            cpuModel: $cpuModel,
            cpuType: $cpuType,
            runtime: $runtime,
            frameworkRuntime: $frameworkRuntime,
            vmID: $vmID
            }' )

echo $jsonString