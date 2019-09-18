# SAAF - Serverless Application Analytics Framework (SAAF)

This project provides coding templates to support tracing FaaS function server infrastructure for code deployments.
A generic Hello World function is provided for each language as a starting point to write infrastructure traceable FaaS functions to enable tracing code containers and hosts (VMs) created by FaaS platform providers for hosting FaaS functions.  This information can help verify the state of infrastructure (COLD vs. WARM) to understand performance results, and help preserve infrastructure for better FaaS performance.

## Table of Contents:

1. [Java Framework](./java_template/README.md)
2. [Java Deployment Tools](./java_template/deploy/README.md)
3. [Python Framework](./python_template/README.md)
4. [Python Deployment Tools](./python_template/deploy/README.md)
5. [Node.js Framework](./nodejs_template/README.md)
6. [Node.js Deployment Tools](./nodejs_template/deploy/README.md)
7. [BASH Framework](./bash_template/README.md)
8. [BASH Deployment Tools](./bash_template/deploy/README.md)

**Example Function:**
```python
from Inspector import *

def myFunction(request):
  
  # Import the module and collect data
  inspector = Inspector()
  inspector.inspectContainer()
  inspector.inspectCPU()
  inspector.addTimeStamp("frameworkRuntime")

  # Add custom message and finish the function
  inspector.addAttribute("message", "Hello " + request['name'] + "!")
  return inspector.finish()
```

**Example Output JSON:**
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

For more detailed descriptions of each variable, please see the documentation for a specific language.

## Supported Platforms and Languages:

| **Platform** | **Node.js** | **Python** | **Java** | **Bash** |
| --- | :---: | :---: | :---: | :---: |
| AWS Lambda | ✔️ | ✔️ | ✔️ | ✔️ |
| Google Cloud Functions | ✔️ | ✔️ | ⏳ | ❌ |
| IBM Cloud Functions | ✔️ | ✔️ | ✔️ | ❌ |
| Azure Functions (Linux) | ✔️ | ✔️ | ❌ | ❌ |
