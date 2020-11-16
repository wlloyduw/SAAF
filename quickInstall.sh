#!/bin/bash

#
# This script is meant to streamline the process of setting up SAAF and FaaS Runner on
# EC2 instances. Simply run the script to download all nessessary dependencies and
# setup each cloud platforms CLI.
# @author Robert Cordingly
#

clear
echo You are about to install everything needed to use SAAF, FaaS Runner, and their helper tools.
echo You will have the option to install and configure each supported FaaS platform\'s CLI.
echo Each installer has some steps to do. This script will pause and give you directions for what you are supposed to do.
echo
read -rsp $'Press any key to continue. Use CTRL+Z to quit at any time.\n' -n1 key

clear
echo
read -p "Would you like to update and upgrade apt? [y/N]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo apt update
    sudo apt upgrade
    echo
    read -rsp $'Finished! Press any key to continue...\n' -n1 key
fi

clear
echo
read -p "Would you like to download SAAF to the current directory? [y/N]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo apt install git
    git clone https://github.com/wlloyduw/SAAF
    echo
    read -rsp $'Repository cloned! Press any key to continue...\n' -n1 key
fi

clear
echo
read -p "Would you like to install dependencies for SAAF and FaaS Runner? [y/N]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo Installing neutral dependencies...
    sudo apt update
    sudo apt upgrade
    sudo apt install parallel bc curl jq python3 python3-pip nodejs npm maven
    pip3 install requests boto3 botocore
    echo
    read -rsp $'Dependencies installed! Press any key to continue...\n' -n1 key
fi

clear
echo
read -p "Would you like to install and setup AWS Lambda? [y/N]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo Installing AWS CLI...
    sudo apt install awscli python3 python3-pip
    pip3 install --upgrade awscli

    clear
    echo Setting up AWS CLI! Get your access keys ready!
    echo
    echo Set region to "us-east-1"
    echo Set output type to "json"
    read -rsp $'Press any key to continue...\n' -n1 key

    aws configure
    echo
    echo Configuration complete! Functions can now be deployed to AWS Lambda.
    read -rsp $'Press any key to continue...\n' -n1 key
fi

clear
echo
read -p "Would you like to install and setup Google Cloud Functions? [y/N]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo Installing GCloud SDK...
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    apt-get install apt-transport-https ca-certificates
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    sudo apt-get update && sudo apt-get install google-cloud-sdk
    sudo apt-get install google-cloud-sdk-app-engine-java

    clear
    echo Setting up GCloud CLI!
    echo
    echo This SDK is more difficult to install than AWS. A browser will open, sign in and allow premissions.
    echo After signed in, return to the Terminal window.
    echo
    echo If asked to choose a project, create a new project.
    echo Name the project to something like uw-tacoma{STUDENT ID}. Projects must have a unique names!
    echo
    echo Google will ask to enable the cloudfunctions API, enter y. It will fail. Enter y again and it will say there was an error again.
    echo This is fine, it should have worked.
    echo
    read -rsp $'Press any key to continue...\n' -n1 key
    gcloud init
    gcloud functions list
    echo
    echo Configuration complete! Functions can now be deployed to Google Cloud Functions.
    read -rsp $'Press any key to continue...\n' -n1 key
fi

clear
echo
read -p "Would you like to install and setup IBM Cloud Functions? [y/N]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo Installing IBM Cloud CLI...
    curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
    ibmcloud update
    ibmcloud plugin install cloud-functions

    clear
    echo Setting up IBM Cloud CLI!
    echo
    echo IBM requires you to login through their CLI.
    echo After logging in, select the us-south region.
    echo
    read -rsp $'Press any key to continue...\n' -n1 key

    ibmcloud login
    ibmcloud plugin install cloud-functions
    ibmcloud target --cf
    ibmcloud target -g Default

    echo
    echo Configuration complete! Functions can now be deployed to IBM Cloud Functions. Your account was configured to use the default Cloud Foundry namespace.
    read -rsp $'Press any key to continue...\n' -n1 key
fi

clear
echo
read -p "Would you like to install and setup Azure Functions? [y/N]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo Installing Azure Functions CLI.
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor >microsoft.gpg
    sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
    sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
    sudo apt-get update
    sudo apt-get install azure-functions-core-tools
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

    clear
    echo Setting up Azure CLI.
    echo
    echo It is simple, a browser will open, login and you are done.
    read -rsp $'Press any key to continue...\n' -n1 key
    az login

    echo
    echo Configuration complete! Functions can now be deployed to Azure.
    read -rsp $'Press any key to continue...\n' -n1 key
fi
