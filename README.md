# SAAF - Serverless Application Analytics Framework

This project provides coding templates to support tracing FaaS function server infrastructure for code deployments.
A generic Hello World function is provided for each language as a starting point to write infrastructure traceable FaaS functions to enable tracing code containers and hosts (VMs) created by FaaS platform providers for hosting FaaS functions.  This information can help verify the state of infrastructure (COLD vs. WARM) to understand performance results, and help preserve infrastructure for better FaaS performance.

SAAF also provides tools to automate the process of deploying functions to AWS Lambda, Google Cloud Functions, IBM Cloud Functions, and Azure Functions. Each language comes with a publish script built to allow functions to be written once and then automatically packaged, deployed, and tested on all supported platforms. This platform-neutral system allows functions to be easily written and compared accross different FaaS platforms, hardware configurations, and deployment options.

### More Articles:

1. [Java Framework](./java_template/)
2. [Java Deployment Tools](./java_template/deploy/)
3. [Python Framework](./python_template/)
4. [Python Deployment Tools](./python_template/deploy/)
5. [Node.js Framework](./nodejs_template/)
6. [Node.js Deployment Tools](./nodejs_template/deploy/)
7. [BASH Framework](./bash_template/)
8. [BASH Deployment Tools](./bash_template/deploy/)
9. [FaaS Runner](./test/)
10. [Research with SAAF](./research.md)

### Quick Install:

Install and setup all of the dependencies, SAAF templates, cloud CLI's, FaaS Runner, and all other tools with one script:
```
curl -O https://raw.githubusercontent.com/wlloyduw/SAAF/master/quickInstall.sh
sudo chmod 777 quickInstall.sh
./quickInstall.sh
```
* quickInstall.sh works with Ubuntu 18.04. All tools also work on MacOS Mohave and should work with the Windows Linux subsystem but all dependencies must be installed manually.

&nbsp;

# Using SAAF in a Function:

Using SAAF in a function is as simple importing the framework and adding a couple lines of code. Attributes collected by SAAF will be appended onto the JSON response. For asynchronous functions, this data could be stored into a database, such as AWS S3, and retrieved after the function is finished.

**Example Function:**

```python
from Inspector import *

def myFunction(request):
  
  # Initialize the Inspector and collect data.
  inspector = Inspector()
  inspector.inspectAll()

  # Add a "Hello World!" message.
  inspector.addAttribute("message", "Hello " + request['name'] + "!")

  # Return attributes collected.
  return inspector.finish()
```

**Example Output JSON:**

The attributes collect can be customized by changing which functions are called. For more detailed descriptions of each variable and the functions that collect them, please see the framework documentation for each language.

```json
{
	"version": 0.2,
	"lang": "python",
	"cpuType": "Intel(R) Xeon(R) Processor @ 2.50GHz",
	"cpuModel": 63,
	"vmuptime": 1551727835,
	"uuid": "d241c618-78d8-48e2-9736-997dc1a931d4",
	"vmID": "tiUCnA",
	"platform": "AWS Lambda",
	"newcontainer": 1,
	"cpuUsrDelta": "904",
	"cpuNiceDelta": "0",
	"cpuKrnDelta": "585",
	"cpuIdleDelta": "82428",
	"cpuIowaitDelta": "226",
	"cpuIrqDelta": "0",
	"cpuSoftIrqDelta": "7",
	"vmcpustealDelta": "1594",
	"frameworkRuntime": 35.72,
	"message": "Hello Fred Smith!",
	"runtime": 38.94
}
```

### Supported FaaS Platforms and Languages:

| **Platform** | **Node.js** | **Python** | **Java** | **Bash** |
| --- | :---: | :---: | :---: | :---: |
| AWS Lambda | ✔️ | ✔️ | ✔️ | ✔️ |
| Google Cloud Functions | ✔️ | ✔️ | ❌ | ❌ |
| IBM Cloud Functions | ✔️ | ✔️ | ✔️ | ❌ |
| Azure Functions (Linux) | ✔️ | ✔️ | ❌ | ❌ |
| OpenFaaS | ❌ | ✔️ | ❌ | ❌ |

&nbsp;

# Deploy Functions Anywhere:

Each language comes with a publish.sh script that can be used to simplify the process of deploying functions and remove the need to visit each cloud provider's website. This script is located in the /deploy folder of each language template. SAAF's deployment tools allow a function to be written once and then automatically packaged, deployed, and tested on each platform. To use the publish script, simply follow the directions below:

1. Install all nessessary dependencies and setup each cloud's provider's CLI.
  This can be done using [quickInstall.sh](./quickInstall.sh)
2. Configure config.json.
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

  For more information about each languages deployment tools, see the README.md in each of the template's deploy folder:
[Java](./java_template/deploy), [Python](./python_template/deploy), [Node.js](./nodejs_template/deploy), [BASH](./bash_template/deploy)

&nbsp;

# Run Experiments with FaaS Runner: 

FaaS Runner is a tool used to create, execute, and automate experiments on FaaS platforms using SAAF. FaaS Runner works by creating function and experiment JSON files that define how to run an experiment, what settings to use, and how to deplay the results. For more information about these JSON files, see the [FaaS Runner Documentation](./test/).

``` bash 
# Using FaaS Runner.
./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: OUTPUT PATH}

# Run the example:
./faas_runner.py -f ./functions/exampleFunction.json -e ./experiments/exampleExperiment.json
```

&nbsp;


**ACKNOWLEDGEMENT**

This material is based upon work supported by the National Science Foundation under Grant Number ([OAC-1849970](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1849970&HistoricalAwards=false)).

Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.
