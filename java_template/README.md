# SAAF - Serverless Application Analytics Framework - Java

SAAF is a programming framework that allows for tracing FaaS function server infrastructure for code deployments. This framework includes functions to enable tracing code containers and hosts (VMs) created by FaaS platform providers for hosting FaaS functions. This information can help verify the state of infrastructure (COLD vs. WARM) to understand performance results, and help preserve infrastructure for better FaaS performance.

### Getting Started

To use the core SAAF framework, download the [Inspector.java](./src/main/java/saaf/Inspector.java) script into an existing Java project and simply import the module as shown below.

SAAF also includes tools to deploy and develop new functions for each supported platform automatically. To make use of these tools, download the entire repository and follow the directions in the [tools directory](./tools). 

### Import the Module into an Existing Project

```java
import saaf.Inspector;
```
Initializing the Inspector should be the first line of your function as it begins recording the runtime.

### Example Hello World Function

```java
public HashMap<String, Object> handleRequest(Request request, Context context) {
  
  //Collect data
  Inspector inspector = new Inspector();
  inspector.inspectCPU();
  inspector.inspectContainer();
  inspector.addTimeStamp("frameworkRuntime");
  
  //Add custom message and finish the function
  inspector.addAttribute("message", "Hello " + request.getName() + "!");
  return inspector.finish();
}
```

#### Example JSON Output

```json
{
  "version": 0.2,
  "lang": "java",
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

# Attributes Collected by Each Function

The amount of data collected is detemined by which functions are called. If some attributes are not needed, then some functions many not need to be called. If you would like to collect every attribute, the inspectAll() method will run all methods.

### Core Attributes

| **Field** | **Description** |
| --------- | --------------- |
| version | The version of the SAAF Framework. |
| lang | The language of the function. |
| runtime | The server-side runtime from when the function is initialized until Inspector.finish() is called. |

### inspectContainer()

| **Field** | **Description** |
| --------- | --------------- |
| uuid | A unique identifier assigned to a container if one does not already exist. |
| newcontainer | Whether a container is new (no assigned uuid) or if it has been used before. |
| vmuptime | Time when the host booted in seconds since January 1, 1970 (Unix epoch). |

### inspectCPU()

| **Field** | **Description** |
| --------- | --------------- |
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
| contextSwitches | The number of times the CPU has switched context since boot. |

### inspectCPUDelta()

| **Field** | **Description** |
| --------- | --------------- |
| cpuUsrDelta | Change in cpuUsr compared to when inspectCPU was called. |
| cpuNiceDelta | Change in cpuNice compared to when inspectCPU was called. |
| cpuKrnDelta | Change in cpuKrn compared to when inspectCPU was called. |
| cpuIdleDelta | Change in cpuIdle compared to when inspectCPU was called. |
| cpuIowaitDelta | Change in cpuIowait compared to when inspectCPU was called. |
| cpuIrqDelta | Change in cpuIrq compared to when inspectCPU was called. |
| cpuSoftIrqDelta | Change in cpuSoftIrq compared to when inspectCPU was called. |
| vmcpustealDelta | Change in vmcpusteal compared to when inspectCPU was called. |
| contextSwitchesDelta | The number of times the CPU has switched context since inspectCPU. |

### inspectMemory()

| **Field** | **Description** |
| --------- | --------------- |
| totalMemory | The total memory, in kB, allocated to the VM. |
| freeMemory | The current amount of free memory in kB. |
| pageFaults | The total number of page faults since boot. |
| majorPageFaults | The total number of major page faults since boot. |

### inspectMemoryDelta()

| **Field** | **Description** |
| --------- | --------------- |
| pageFaultsDelta | The total number of page faults since inspectMemory. |
| majorPageFaultsDelta | The total number of major page faults since inspectMemory. |

### inspectPlatform()

| **Field** | **Description** |
| --------- | --------------- |
| platform | The FaaS platform hosting this function. |
| containerID | A platform specific container identifier. Supported on AWS Lambda and Azure Functions. |
| vmID | A platform specific virtual machine identifier. Supported on AWS Lambda. |

### inspectLinux()

| **Field** | **Description** |
| --------- | --------------- |
| linuxVersion | The version of the linux kernel. |

# Helper Functions

### finish()

This should be the last method called. It will return the final object containing all of the attributes collected.

### inspectAll()

Calls all inital inspect methods such as inspectPlatform, inspectCPU, ect. Should be called immediately after initalizing the Inspector.

### inspectAllDeltas()

Calls all methods that calculate deltas, such as inspectCPUDelta. This should be called at the end of your function, before calling the finish() method.

### addAttribute(key, value)

Add a custom attribute to the data return by SAAF. 

### getAttribute(key)

Get an attribute already stored in SAAF.

### addTimeStamp(key)

Add a custom time stamp to SAAF. This will store the time in ms from when SAAF started to when this method was called.

### consumeResponse(response)

If using a POJO response object, use this method to pull the attributes from the object and add them to SAAF.

&nbsp;
