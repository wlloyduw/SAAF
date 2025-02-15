# SAAF Deployment Tools - Java

One goal of SAAF is to support multiple FaaS platforms. Currently AWS Lambda, Google Cloud Functions, IBM Cloud Functions/OpenWhisk, and Azure Function are the supported platforms. A few scripts have been developed to aid in development, deployment, and testing of each platform.

### Project Structure
The project structure is meant to simplify deploying onto each of the supported platforms.

    📁 java_template
        📁 src/main/java
            📁 ibm
                Hello.java
            📁 lambda
                Hello.java
                HelloPOJO.java
                Request.java
            📁 local
                Local.java
            📁 saaf
                Inspector.java
                Response.java
        📁 deploy
            config.json
            publish.sh
  

### 📁 src Folder

The src folder contains all of the code for your function. 

  * [**Inspector.java**](../src/main/java/saaf/Inspector.java) is the SAAF itself and is completely independent of any files or folders in this project. If you do not plan to use this file sctructure, the saaf package can be moved into any Java project.

  * [**lambda/Hello.java**](../src/main/java/lambda/Hello.java) and [**ibm/Hello.java**](../src/main/java/ibm/Hello.java) are the handler classes that will be called by each platform.
    - If you perfer using POJOs for requests, refactor [**lambda/HelloPOJO.java**](../src/main/java/lambda/HelloPOJO.java) into **lambda/Hello.java** and define parameter getters and setters in [**lambda/Request.java**](../src/main/java/lambda/Request.java)
  
  * [**Response.java**](../src/main/java/saaf/Response.java) if you prefer using POJOs over Hashmaps to represent request JSON, you can use this class for your response and then add all of it's attributes to the output by calling the *Insector.consumeResponse()* method.
    
### 📁 deploy Folder

This folder contains tools to help deploy serverless functions onto each supported platform. For more detailed documentation please see the comments at the beginning of each file. 

  * [**publish.sh**](./publish.sh) is a script used to deploy a function onto each platform. This requires each each cloud providers CLI to be installed and properly configured.

  * [**config.json**](./config.json) contains all of the neccessary variables to deploy a function and is used by [publish.sh](./publish.sh).
    * **functionName:** The name of your function. 
    * **AWS Lambda Attributes**:
      * **lambdaHandler:** The package, class, and method to use as the function handler.
      * **lambdaRoleARN:** The ARN of the AWS Lambda role to use.
      * **lambdaSubnets:** The VPC subnet to use. This is optional and can be left blank.
      * **lambdaSecurityGroups:** The VPC security group to use. This is optional and can be left blank.
    * **IBM Cloud Functions Attributes**:
      * **ibmHandler:** The package and class to use as the function handler.

    * **test:** After a function is deployed, this payload will be use to automatically test the function.


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

## Multiple Configuration Files

If you want to use more than one configuration file you can supply a path to a file as the optional last command line argument.

``` bash 
./publish.sh 1 1 1 1 128 ./otherConfig.json
```