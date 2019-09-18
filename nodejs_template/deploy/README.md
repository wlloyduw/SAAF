# SAAF Deployment Tools

One goal of SAAF is to support multiple FaaS platforms. Currently AWS Lambda, Google Cloud Functions, IBM Cloud Functions/OpenWhisk, and Azure Function are the supported platforms. A few scripts have been developed to aid in development, deployment, and testing of each platform.

### Project Structure
The project structure is meant to simplify deploying onto each of the supported platforms.

    📁 nodejs_template
        📁 src
            function.js
            Inspector.js
            package.json
        📁 deploy
            📁 node_modules
                ...
            config.json
            publish.sh
            local.js
        📁 platforms  
            ...
  

### 📁 src Folder

The src folder contains all of the code for your function. 

  * [**Inspector.js**](../src/Inspector.js) is the SAAF itself and is completely independent of any files or folders in this project. If you do not plan to use this file sctructure, Inspector.js can be used and moved to any Node.js project.
  
  * [**function.js**](../src/function.js) file is the handler that each cloud provider will execute. 

  * [**package.json**](../src/package.json) is where 3rd party dependencies must be defined. 
      (**WARNING:** If you are deploying onto Azure Functions, dependencies must also be downloaded into deploy/node_modules)
    
### 📁 deploy Folder

This folder contains tools to help deploy serverless functions onto each supported platform. For more detailed documentation please see the comments at the beginning of each file. 

  * [**publish.sh**](./publish.sh) is a script used to deploy a function onto each platform. This requires each each cloud providers CLI to be installed and properly configured.

  * [**config.json**](./config.json) contains all of the neccessary variables to deploy a function and is used by [publish.sh](./publish.sh).
    * **functionName:** The name of your function. 
        - On Azure, this will be used for all other resources such as Function App, Storage and Resource Groups. 
            Must be lowercase alphanumeric, and unique.
    * **lambdaRoleARN:** The ARN of the AWS Lambda role to use.
    * **lambdaSubnets:** The VPC subnet to use. This is optional and can be left blank.
    * **lambdaSecurityGroups:** The VPC security group to use. This is optional and can be left blank.
    * **test:** After a function is deployed, this payload will be use to automatically test the function.

  * [**node_modules**](./node_modules) contains any dependencies your function may need. Any modules installed here will be deployed with your function. 
    Modules may need to be defined in [/src/package.json](../src/package.json) depending on the platform.

  * [**local.js**](./local.js) is an additional handler used to execute a function locally. This can be useful to test a function before deploying onto the cloud.
    
### 📁 platforms Folder

This folder contains all of the platform specific files needed to deploy onto each cloud provider. NONE of these files need to be edited to deploy a function. The publish.sh script copies these files into the src folder, constructs the correct folder structure, deploys the function, and then cleans up the src folder back to its original state.


# Using [publish.sh](./publish.sh):

The publish script is meant to simplify the process of deploying functions and remove the need to visit each cloud provider's website. SAAF's deployment tools allow a function to be written once and then automatically packaged, deployed, and tested on each platform. To use the publish script, simply follow the directions below:

1. Install all nessessary dependencies and setup each cloud's provider's CLI.
  This can be done using [.../quickInstall.sh](.../quickInstall.sh)
2. Configure [config.json](./config.json)
  Fill in the name of your function, a AWS ARN (if deploying to AWS Lambda), and choose a payload to test your function with.
3. Run the script. 
  The script takes 5 parameters, the first four are booleans that determine what platforms to deploy to and the final is a memory setting to use on supported platforms.

### Example Usage:
``` bash 
# Description of Parameters
./publish.sh AWS GOOGLE IBM AZURE Memory

# Deploy to AWS and Azure with 512 MBs
./publish.sh 1 0 0 1 512

# Deploy to Google and IBM with 1GB.
./publish.sh 0 1 1 0 1024

# Deploy to all platforms with 128 MBs:
./publish.sh 1 1 1 1 128

# Deploy to AWS with 3GBs:
./publish.sh 1 0 0 0 3008
```
