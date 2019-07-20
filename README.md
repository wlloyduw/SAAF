# SAAF - Serverless Application Analytics Framework (SAAF)

This project provides coding templates to support tracing FaaS function server infrastructure for code deployments.
A generic Hello World function is provided for different FaaS platform/language combinations as a starting point to write infrastructure traceable FaaS functions to enable tracing code containers and hosts (VMs) created by FaaS platform providers for hosting FaaS functions.  This information can help verify the state of infrastructure (COLD vs. WARM) to understand performance results, and help preserve infrastructure for better FaaS performance.

**Example Input JSON:**
```json
{
	"Name": "Fred Smith"
}
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
	"newcontainer": 1,
	"cpuUsr": "904",
	"cpuNice": "0",
	"cpuKrn": "585",
	"cpuIdle": "82428",
	"cpuIowait": "226",
	"cpuIrq": "0",
	"cpuSoftIrq": "7",
	"vmcpusteal": "1594",
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