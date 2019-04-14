# Faas Inspector

FaaS Inspector is a programming framework that allows for tracing FaaS function server infrastructure for code deployments. This framework includes functions to enable tracing code containers and hosts (VMs) created by FaaS platform providers for hosting FaaS functions. This information can help verify the state of infrastructure (COLD vs. WARM) to understand performance results, and help preserve infrastructure for better FaaS performance.

### Getting Started

To use the core FaaS Inspector framework, download the [Inspector.java](./src/main/java/faasinspector/Inspector.java) script into an existing Java project and simply import the module as shown below.

FaaS Inspector also includes tools to deploy and develop new functions for each supported platform automatically. To make use of these tools, download the entire repository and follow the directions in the [tools directory](./tools). 

### Import the Module into an Existing Project

```java
import faasinspector.Inspector;
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

The amount of data collected is detemined by which functions are called. If some attributes are not needed, then some functions many not need to be called.

### Core Attributes

| **Field** | **Description** |
| --------- | --------------- |
| version | The version of the FaaS Inspector Framework. |
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
| vmcpusteal | Time spent waiting for real CPU while hypervisor is using another virtual CPU. |

### inspectPlatform()

| **Field** | **Description** |
| --------- | --------------- |
| platform | The FaaS platform hosting this function. |

### inspectLinux()

| **Field** | **Description** |
| --------- | --------------- |
| linuxVersion | The version of the linux kernel. |

&nbsp;
