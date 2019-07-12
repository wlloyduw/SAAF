#!/bin/bash

CPUMetrics=$(cat /proc/stat | grep "^cpu" | head -1)

IFS=' ' read -r -a metricArray <<< "$CPUMetrics"
for element in "${metricArray[@]}"
do
    echo "$element"
done

echo $(./dependencies/uuid)

echo $CPUMetrics