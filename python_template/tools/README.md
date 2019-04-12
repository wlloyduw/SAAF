# Faas Inspector Deployment Tools

One goal of FaaS Inspector is to support multiple FaaS platforms. Currently AWS Lambda, Google Cloud Functions, IBM Cloud Functions/OpenWhisk, and Azure Function are the supported platforms. A few scripts have been developed to aid in development, deployment, and testing of each platform.

### Project Structure
The project structure is meant to simplify deploying onto each of the supported platforms.

    📁 python_template
        📁 src
            handler.py
            Inspector.py
        📁 tools
            config.json
            publish.sh
        📁 platforms  
            ...
  

### 📁 src Folder

The src folder contains all of the code for your function. 

  * [**Inspector.py**](../src/Inspector.py) is the FaaS Inspector itself and is completely independent of any files or folders in this project. If you do not plan to use this file sctructure, Inspector.py can be used and moved to any Python project.
  
  * [**handler.py**](../src/handler.py) file is the handler that each cloud provider will execute. 
    
### 📁 tools Folder

This folder contains tools to help deploy serverless functions onto each supported platform. For more detailed documentation please see the comments at the beginning of each file. 

  * [**config.json**](./config.json) contains all of the neccessary variables to deploy a function. This includes the name of the function, the Azure Function app name, and other information.
  * [**publish.sh**](./publish.sh) is a script used to deploy a function onto each platform. This requires each each cloud providers CLI to be installed and properly configured.
    
### 📁 platforms Folder

This folder contains all of the platform specific files needed to deploy onto each cloud provider. NONE of these files need to be edited to deploy a function. The publish.sh script copies these files into the src folder, constructs the correct folder structure, deploys the function, and then cleans up the src folder back to its original state.
