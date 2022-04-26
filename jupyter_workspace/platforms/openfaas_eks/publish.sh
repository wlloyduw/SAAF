#!/bin/bash

location=$1
cd "$location" || exit

echo "Publish: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
cluster=$(jq '.cluster_name' < ./config.json | tr -d '"')
password=$(jq '.open_faas_password' < ./config.json | tr -d '"')
gateway=$(jq '.gateway' < ./config.json | tr -d '"')
image_repo=$(jq '.image_repo' < ./config.json | tr -d '"')
memory=$(jq '.memory' < ./config.json | tr -d '"')
cpu=$(jq '.cpu' < ./config.json | tr -d '"')
timeout=$(jq '.timeout' < ./config.json | tr -d '"')

echo "Publish: Creating yaml file..."

echo "version: 1.0" > ./.build/$function.yml
echo "provider:" >> ./.build/$function.yml
echo "  name: openfaas" >> ./.build/$function.yml
echo "  gateway: $gateway" >> ./.build/$function.yml
echo "functions:" >> ./.build/$function.yml
echo "  $function:" >> ./.build/$function.yml
echo "    lang: python3-debian" >> ./.build/$function.yml
echo "    handler: ./$function" >> ./.build/$function.yml
echo "    image: $image_repo:$function" >> ./.build/$function.yml
echo "    limits:" >> ./.build/$function.yml
echo "      memory: $(echo $memory)Mi" >> ./.build/$function.yml
echo "      cpu: $(echo $cpu)m" >> ./.build/$function.yml
echo "    environment:" >> ./.build/$function.yml
echo "      read_timeout: \"$(echo $timeout)s\"" >> ./.build/$function.yml
echo "      write_timeout: \"$(echo $timeout)s\"" >> ./.build/$function.yml
echo "      exec_timeout: \"$(echo $timeout)s\"" >> ./.build/$function.yml

export KUBECONFIG=~/.kube/eksctl/clusters/$cluster
export OPENFAAS_URL=$gateway

cd ./.build || exit

echo $password | faas-cli login --username admin --password-stdin
faas-cli remove -f $function.yml || echo "Function not deployed..."
faas-cli up -f $function.yml

