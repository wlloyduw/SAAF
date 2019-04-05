# Faas Inspector TestingOne goal of FaaS Inspector is to support multiple FaaS platforms. Currently AWS Lambda, Google Cloud Functions, IBM Cloud Functions/OpenWhisk, and Azure Function are the supported platform. A few scripts have been developed to aid in development, deployment, and testing of each platform.### Project StructureThe project structure is meant to simplify deploying onto each of the supported platforms.

  📁 nodejs_template
    📁 platforms
      ...
    📁 scr
      function.js
      Inspector.js
      package.json
    📁 test
      📁 node_modules
        ...
      config.json
      local.js
      test.sh
      publish.js
  ### 📁 platforms Folder

This folder contains all of the platform specific files needed to deploy onto each cloud provider. NONE of these files need to be edited to deploy a function. The publish.sh script copies these files into the scr folder, constructs the correct folder structure, deploys the function, and then cleans up the scr folder back to its original state.

### 📁 scr Folder

The scr folder contains all of the code for your function. 

  **Inspector.js** is the FaaS Inspector itself and is completely independent of any files or folders in this project. If you do not plan to use this file sctructure, Inspector.js can be used and moved to any Node.js project.
  
  **function.js** file is the handler that each cloud provider will execute. 
  
  **package.json** is where 3rd party dependencies must be defined (*WARNING:* If you are deploying onto Azure Functions, depencies must also be downloaded into test/node_modules). 

### 📁 test Folder