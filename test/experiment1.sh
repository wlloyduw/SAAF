#!/bin/bash

# FaaS Programming Languages Comparison Experiment 1
# @author Robert Cordingly

args="--runs 1 --threads 1 --warmupBuffer 0 --combineSheets 0 --sleepTime 0 --openCSV 0"

dataSize=100
bucket="project.fall19.tcss562.vmp"
endpoint="python.cluster-ctutcfcxozkc.us-east-1.rds.amazonaws.com"
name="DB_TCSS562"

subFolder="experiment1_results"
mkdir ./$subFolder

for lang in Python Java Go
do
    aws lambda update-function-configuration --function-name ServiceOne$lang --memory-size 3008
    aws lambda update-function-configuration --function-name ServiceTwo$lang --memory-size 3008
    aws lambda update-function-configuration --function-name ServiceThree$lang --memory-size 3008
done

for dataSize in 100
do
    mkdir ./$subFolder/results$dataSize
    for lang in Java
    do
        mkdir ./$subFolder/results$dataSize/$lang

        payload1="[{\"bucketname\":\"$bucket\",\"key\":\"${dataSize}_Sales_Records.csv\"}]"
        payload2="[{\"bucketname\":\"$bucket\",\"key\":\"edited_${dataSize}_Sales_Records.csv\",\"tablename\":\"SalesData\",\"batchSize\": 1000,\"dbEndpoint\":\"$endpoint\",\"dbName\":\"$name\"}]"
        payload3="[{\"bucketname\":\"$bucket\",\"key\":\"QueryResults.csv\",\"tablename\":\"SalesData\",\"stressTestLoops\": 1,\"dbEndpoint\":\"$endpoint\",\"dbName\":\"$name\"}]"

        echo
        echo "Running FaaS Runner for Experiment..."
        echo
        functions="--function[0] ServiceOne$lang --function[1] ServiceTwo$lang --function[2] ServiceThree$lang"
        payloads="--payloads[0] $payload1 --payloads[1] $payload2 --payloads[2] $payload3"

        ./faas_runner.py -o ./$subFolder/results$dataSize/$lang $functions $payloads $args
    done
done

echo "Experiments Done!"