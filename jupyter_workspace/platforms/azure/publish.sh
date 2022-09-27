#!/bin/bash

location=$1
cd "$location" || exit

echo "Publish: Loading config..."
function=$(jq '.function_name' < ./config.json | tr -d '"')
runtime=$(jq '.runtime' < ./config.json | tr -d '"')

cd ./.build || exit

echo "Publish: Creating resources..."
az group create --name $function --location eastus
az storage account create --name $function --location eastus --resource-group $function --sku Standard_LRS
az resource create -g $function -n $function --resource-type "Microsoft.Insights/components" --properties "{\"Application_Type\":\"web\"}"
az functionapp create --resource-group $function --consumption-plan-location eastus --name $function --runtime $runtime --os-type Linux --output json --storage-account $function --app-insights $function --functions-version 2

echo "Publish: Deploying function..."
python3 -m venv .env
source .env/bin/activate
func azure functionapp publish $function --force
deactivate