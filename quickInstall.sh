#!/bin/bash

echo You are about to install EVERYTHING needed to deploy FaaS Functions to AWS Lambda, Google Cloud Functions, IBM Cloud Functions, and Azure Functions.
echo This has a lot of things so get ready to type Y many times.
echo Each installer has some steps to do. This script will pause and give you directions for what you are supposed to do.
read -rsp $'Press any key to continue...\n' -n1 key

echo Installing dependencies...
sudo apt update
sudo apt upgrade
sudo apt install parallel bc curl jq python3 python3-pip nodejs npm maven
pip3 install requests

echo Installing AWS CLI...
sudo apt install awscli

clear
echo Setting up AWS CLI! Get your access keys ready!
echo Set region to "us-east-1"
echo Set output type to "json"
read -rsp $'Press any key to continue...\n' -n1 key

aws configure
echo Configuration complete! Functions can now be deployed to AWS Lambda.
read -rsp $'Press any key to continue...\n' -n1 key

echo Installing GCloud SDK...
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
apt-get install apt-transport-https ca-certificates
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk
sudo apt-get install google-cloud-sdk-app-engine-java

clear
echo Setting up GCloud CLI!
echo This SDK is easier to install than AWS. A browser will open, sign in and allow premissions.
echo If asked to choose a project, create a new project.
echo Name the project "uw-tacoma-project"
echo Google will ask to enable the cloudfunctions API, enter y. It will retry again, enter y again and next will say there was an error. THIS IS FINE it should have worked anyway.
read -rsp $'Press any key to continue...\n' -n1 key
gcloud init
gcloud functions list
echo Configuration complete! Functions can now be deployed to Google Cloud Functions.
read -rsp $'Press any key to continue...\n' -n1 key

echo Installing IBM Cloud CLI...
curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
ibmcloud update
ibmcloud plugin install cloud-functions

clear
echo Setting up IBM Cloud CLI!
read -rsp $'Press any key to continue...\n' -n1 key
ibmcloud login -a
ibmcloud target -o <org> -s <space> 

echo Configuration not complete... IBM requires you to login by typing your email and password into the command line. You are going to have to do that yourself. I am very sorry...
read -rsp $'Press any key to continue...\n' -n1 key

echo Installing Azure Functions CLI.
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

clear
echo Setting up Azure CLI. It is simple, a browser will open, login and you are done.
az login


echo Congratulations! You have installed everything needed to use SaaF, FaaS Runner, and all of their helper scripts. 


