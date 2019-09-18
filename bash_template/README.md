# SAAF - Serverless Application Analytics Framework - BASH

SAAF is a programming framework that allows for tracing FaaS function server infrastructure for code deployments. This framework includes functions to enable tracing code containers and hosts (VMs) created by FaaS platform providers for hosting FaaS functions. This information can help verify the state of infrastructure (COLD vs. WARM) to understand performance results, and help preserve infrastructure for better FaaS performance.

### Getting Started

To use the core SAAF framework, download the [bootstrap](./src/bootstrap) script into an existing Lambda custom runtime.

SAAF also includes tools to deploy and develop new functions for each supported platform automatically. To make use of these tools, download the entire repository and follow the directions in the [deploy directory](./deploy). 

### Import the Module into an Existing Project

Using SAAF with AWS Lambda custom runtimes is as simple as deploying a project with the custom SAAF [bootstrap](./src/bootstrap) file. 

### Example Hello World Function

```bash
function handler () {
  EVENT_DATA=$1
  echo "$EVENT_DATA" 1>&2;
  
  name=$(echo $EVENT_DATA | ./dependencies/jq-linux64.dms '.name' | tail -c +2 | head -c -2)
  RESPONSE="Hello $name!"
  echo $RESPONSE
}
```

#### Example JSON Output

```json
{
  "version": 0.1,
  "lang": "bash",
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
  "message": "Hello Bob!",
  "runtime": 38.94
}
```
&nbsp;

### Attributes Collected

| **Field** | **Description** |
| --------- | --------------- |
| version | The version of the SAAF Framework. |
| lang | The language of the function. |
| runtime | The server-side runtime from when the function is initialized until Inspector.finish() is called. |
| uuid | A unique identifier assigned to a container if one does not already exist. |
| newcontainer | Whether a container is new (no assigned uuid) or if it has been used before. |
| vmuptime | Time when the host booted in seconds since January 1, 1970 (Unix epoch). |
| cpuType | The model name of the CPU. |
| cpuModel | The model number of the CPU. |
| cpuUsr | Time spent normally executing in user mode. |
| cpuNice | Time spent executing niced processes in user mode. |
| cpuKrn | Time spent executing processes in kernel mode. |
| cpuIdle | Time spent idle. |
| cpuIowait | Time spent waiting for I/O to complete. |
| cpuIrq | Time spent servicing interrupts. |
| cpuSoftIrq | Time spent servicing software interrupts. |
| vmcpusteal | Cycles spent waiting for real CPU while hypervisor is using another virtual CPU. |
| cpuUsrDelta | Change in cpuUsr compared to when inspectCPU was called. |
| cpuNiceDelta | Change in cpuNice compared to when inspectCPU was called. |
| cpuKrnDelta | Change in cpuKrn compared to when inspectCPU was called. |
| cpuIdleDelta | Change in cpuIdle compared to when inspectCPU was called. |
| cpuIowaitDelta | Change in cpuIowait compared to when inspectCPU was called. |
| cpuIrqDelta | Change in cpuIrq compared to when inspectCPU was called. |
| cpuSoftIrqDelta | Change in cpuSoftIrq compared to when inspectCPU was called. |
| vmcpustealDelta | Change in vmcpusteal compared to when inspectCPU was called. |
| platform | The FaaS platform hosting this function. |
| containerID | A platform specific container identifier. Supported on AWS Lambda and Azure Functions. |
| vmID | A platform specific virtual machine identifier. Supported on AWS Lambda. |
| linuxVersion | The version of the linux kernel. |

&nbsp;
