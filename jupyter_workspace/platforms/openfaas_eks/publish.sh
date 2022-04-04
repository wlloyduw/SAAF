#!/bin/bash

location=$1
cd "$location" || exit

echo "Publish: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
cluster=$(jq '.cluster_name' < ./config.json | tr -d '"')
password=$(jq '.open_faas_password' < ./config.json | tr -d '"')
gateway=$(jq '.gateway' < ./config.json | tr -d '"')

export KUBECONFIG=~/.kube/eksctl/clusters/$cluster
export OPENFAAS_URL=$gateway

cd ./.build || exit

echo $password | faas-cli login --username admin --password-stdin
faas-cli remove -f $function.yml || echo "Function not deployed..."
faas-cli up -f $function.yml

