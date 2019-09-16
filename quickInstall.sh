#!/bin/bash

echo You are about to install everything needed to use SAAF, FaaS Runner, and their helper tools.
echo You will have the option to install and configure each supported FaaS platform\'s CLI.
echo Each installer has some steps to do. This script will pause and give you directions for what you are supposed to do.
read -rsp $'Press any key to continue. Use CTRL+Z to quit at any time.\n' -n1 key

read -p "Would you like to download SAAF to the current directory? [y/n]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo apt install git
    git clone https://github.com/RCordingly/SAAF
fi

read -p "Would you like to install dependencies for SAAF and FaaS Runner? [y/n]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo Installing neutral dependencies...
    sudo apt update
    sudo apt upgrade
    sudo apt install parallel bc curl jq python3 python3-pip nodejs npm maven
    pip3 install requests boto3 botocore
fi

read -p "Would you like to install and setup AWS Lambda? [y/n]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
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
fi

read -p "Would you like to install and setup Google Cloud Functions? [y/n]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
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
fi

read -p "Would you like to install and setup IBM Cloud Functions? [y/n]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo Installing IBM Cloud CLI...
    curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
    ibmcloud update
    ibmcloud plugin install cloud-functions

    clear
    echo Setting up IBM Cloud CLI!
    echo IBM requires you to login through their CLI.
    echo This script will ask you for your IBM email and password and will call "imbcloud login -a" to log in.
    echo This script WILL NOT retry if you type something wrong! Make sure it is perfect.
    read -rsp $'Press any key to continue...\n' -n1 key

    echo Please enter your IBM Cloud email address...
    read ibmEmail

    echo Please enter your password...
    read ibmPassword

    ibmcloud login -a $ibmEmail $ibmPassword
    ibmcloud plugin install cloud-functions
    ibmcloud target --cf

    echo Configuration complete! Functions can now be deployed to IBM Cloud Functions. Your account was configured to use the default Cloud Foundry namespace.
    read -rsp $'Press any key to continue...\n' -n1 key
fi

read -p "Would you like to install and setup Azure Functions? [y/n]" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo Installing Azure Functions CLI.
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
    sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
    sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
    sudo apt-get update
    sudo apt-get install azure-functions-core-tools
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

    clear
    echo Setting up Azure CLI. It is simple, a browser will open, login and you are done.
    read -rsp $'Press any key to continue...\n' -n1 key
    az login
fi


echo Congratulations! You have installed everything needed to use SaaF, FaaS Runner, and all of their helper scripts. 


