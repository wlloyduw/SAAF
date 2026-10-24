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
  inspector.inspectAll();
  
  //Add custom message and finish the function
  inspector.addAttribute("message", "Hello " + request.getName() + "!");

  inspector.inspectAllDeltas();
  return inspector.finish();
}
```

#### Example JSON Output

The cpuInfo attribute is omitted for brevity.

```json
{
  "version": 0.8,
  "lang": "java",
  "startTime": 1792804314966,
  "invocations": 1,
  "initializationTime": 1792804314959,
  "uuid": "5eb04f0b-4312-46ec-bf33-5bbd4ee6cd81",
  "newcontainer": 1,
  "cpuType": "Intel(R) Xeon(R) Processor @ 2.80GHz",
  "cpuModel": "85",
  "architecture": "x86",
  "cpuCores": 4,
  "platform": "Unknown Platform",
  "linuxVersion": "Linux vm 6.18.44-fc-v153 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux",
  "totalMemory": 16477348,
  "freeMemory": 15749404,
  "pageFaults": 322066,
  "majorPageFaults": 1404,
  "cpuUser": 13320.0,
  "cpuNice": 0.0,
  "cpuKernel": 7420.0,
  "cpuIdle": 2122540.0,
  "cpuIOWait": 980.0,
  "cpuIrq": 0.0,
  "cpuSoftIrq": 790.0,
  "cpuSteal": 1050.0,
  "cpuGuest": 0.0,
  "cpuGuestNice": 0.0,
  "bootTime": 1792803777,
  "frameworkRuntime": 12,
  "message": "Hello Bob!",
  "userRuntime": 0,
  "cpuUserDelta": 0.0,
  "cpuNiceDelta": 0.0,
  "cpuKernelDelta": 0.0,
  "cpuIdleDelta": 0.0,
  "cpuIOWaitDelta": 0.0,
  "cpuIrqDelta": 0.0,
  "cpuSoftIrqDelta": 0.0,
  "cpuStealDelta": 0.0,
  "cpuGuestDelta": 0.0,
  "cpuGuestNiceDelta": 0.0,
  "pageFaultsDelta": 48,
  "majorPageFaultsDelta": 0,
  "frameworkRuntimeDeltas": 0,
  "runtime": 12,
  "endTime": 1792804314978
}
```
&nbsp;

# Attributes Collected by Each Function

The amount of data collected is detemined by which functions are called. If some attributes are not needed, then some functions many not need to be called. If you would like to collect most attributes, the inspectAll() method will run all of the inspect methods except inspectEnvironment().

### Core Attributes

| **Field** | **Description** |
| --------- | --------------- |
| version | The version of the SAAF Framework. |
| lang | The language of the function. |
| runtime | The server-side runtime from when the function is initialized until Inspector.finish() is called. |
| startTime | The Unix Epoch that the Inspector was initialized in ms. |
| invocations | The number of times an Inspector has been initialized in this function instance. 1 means this is the first invocation the instance has served. |
| initializationTime | The Unix Epoch in ms when SAAF was first loaded by the function instance. This stays the same for every invocation served by the instance. |

### inspectContainer()

| **Field** | **Description** |
| --------- | --------------- |
| uuid | A unique identifier assigned to a container if one does not already exist. |
| newcontainer | Whether a container is new (no assigned uuid) or if it has been used before. |

### inspectCPUInfo()

| **Field** | **Description** |
| --------- | --------------- |
| cpuType | The model name of the CPU. Only reported on x86 CPUs. |
| cpuModel | The model number of the CPU. |
| architecture | The architecture of the CPU, either x86 or arm64. |
| cpuCores | The number of vCPUs available to the function instance. |
| cpuInfo | A list containing every attribute in /proc/cpuinfo for each vCPU. |

### inspectCPU()

CPU times are read from /proc/stat, are the sum of all vCPUs since the host booted, and are converted from ticks into ms.

| **Field** | **Description** |
| --------- | --------------- |
| cpuUser | Time spent normally executing in user mode. |
| cpuNice | Time spent executing niced processes in user mode. |
| cpuKernel | Time spent executing processes in kernel mode. |
| cpuIdle | Time spent idle. |
| cpuIOWait | Time spent waiting for I/O to complete. |
| cpuIrq | Time spent servicing interrupts. |
| cpuSoftIrq | Time spent servicing software interrupts. |
| cpuSteal | Time spent waiting for real CPU while hypervisor is using another virtual CPU. |
| cpuGuest | Time spent running a virtual CPU for guest operating systems. |
| cpuGuestNice | Time spent running a niced guest. |
| bootTime | Time when the host booted in seconds since January 1, 1970 (Unix epoch). |

### inspectCPUDelta()

| **Field** | **Description** |
| --------- | --------------- |
| cpuUserDelta | Change in cpuUser compared to when inspectCPU was called. |
| cpuNiceDelta | Change in cpuNice compared to when inspectCPU was called. |
| cpuKernelDelta | Change in cpuKernel compared to when inspectCPU was called. |
| cpuIdleDelta | Change in cpuIdle compared to when inspectCPU was called. |
| cpuIOWaitDelta | Change in cpuIOWait compared to when inspectCPU was called. |
| cpuIrqDelta | Change in cpuIrq compared to when inspectCPU was called. |
| cpuSoftIrqDelta | Change in cpuSoftIrq compared to when inspectCPU was called. |
| cpuStealDelta | Change in cpuSteal compared to when inspectCPU was called. |
| cpuGuestDelta | Change in cpuGuest compared to when inspectCPU was called. |
| cpuGuestNiceDelta | Change in cpuGuestNice compared to when inspectCPU was called. |

### pollCPUStats() and processCPUPolls()

pollCPUStats() records a snapshot of /proc/stat. inspectCPU() and inspectCPUDelta() call it automatically, and it can be called any number of times in between to sample CPU usage over the course of a function. processCPUPolls() adds every snapshot to the output.

| **Field** | **Description** |
| --------- | --------------- |
| cpuPolls | A list of every /proc/stat snapshot. Each snapshot includes the time it was taken in ms, the CPU times in ms of all vCPUs (cpuTotal) and of each vCPU (cpu0, cpu1, ...), and the remaining /proc/stat counters such as ctxt (context switches) and btime. |

### inspectMemory()

| **Field** | **Description** |
| --------- | --------------- |
| totalMemory | Total memory allocated to the function instance in kB. |
| freeMemory | Current free memory in kB when inspectMemory is called. |
| pageFaults | Total number of page faults experiences by the function instance since boot. |
| majorPageFaults | Total number of major page faults experiences by the function instance since boot. |

### inspectMemoryDelta()

| **Field** | **Description** |
| --------- | --------------- |
| pageFaultsDelta | Change in page faults since inspectMemory was called. |
| majorPageFaultsDelta | Change in major page faults since inspectMemory was called. |

### inspectPlatform()

These attributes are dependent on the FaaS platform. On some platforms not all metrics will be returned.

| **Field** | **Description** |
| --------- | --------------- |
| platform | The FaaS platform hosting this function. |
| containerID | A platform specific container identifier. |
| vmID | A platform specific virtual machine identifier. |
| functionName | The name of the function on the FaaS platform. |
| functionMemory | The configured memory setting on the FaaS Platform. |
| functionRegion | The cloud platform's region the function is deployed to. |
| http_host | OpenFaaS only. The host the request was sent to. |
| http_foward | OpenFaaS only. The X-Forwarded-For header of the request. |
| http_start_time | OpenFaaS only. The X-Start-Time header of the request. |
| host_name | OpenFaaS only. The host name of the pod running the function. |

### inspectLinux()

| **Field** | **Description** |
| --------- | --------------- |
| linuxVersion | The version of the linux kernel. |

### inspectEnvironment()

Adds every environment variable to the output as an attribute, using the name of the variable as the key. A variable with the same name as another attribute will overwrite it. This method is not called by inspectAll().

**Warning:** Environment variables may contain secrets. On AWS Lambda this includes the function's temporary credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN), which will be returned to anyone that can call the function. Only use this method when the output of the function is kept private.

# Helper Functions

### finish(*optional* reponse)

This should be the last method called. It will return the final object containing all of the attributes collected. If using a SAAF response object, the object can be passed into this function to be consumed and merged with the attributes map. To match other languages, it is preferred to use the addAttribute method to append to the response rather than using reponse objects.

| **Field** | **Description** |
| --------- | --------------- |
| runtime | The overall runtime of the function from start to finish in ms. |
| endTime | The Unix Epoch in ms at the end of the function invocation. |

### inspectAll()

Calls all initial inspect methods such as inspectPlatform, inspectCPU, ect. Should be called immediately after initializing the Inspector.

| **Field** | **Description** |
| --------- | --------------- |
| frameworkRuntime | The time in ms to calculate all initial metrics. |

### inspectAllDeltas()

Calls all methods that calculate deltas, such as inspectCPUDelta. This should be called at the end of your function, before calling the finish() method. This will automatically calculate frameworkRuntimeDeltas. On AWS Lambda, this will also estimate the CPU utilization of the function and recommend a memory setting.

| **Field** | **Description** |
| --------- | --------------- |
| userRuntime | The time in ms between when frameworkRuntime is calculated and when inspectAllDeltas is called. This attribute is meant to calculate the time executing user code, not SAAF data collection. |
| frameworkRuntimeDeltas | The time in ms used to collect metric deltas. |
| availableCPUs | AWS Lambda only. The number of vCPUs available at the function's memory setting. |
| utilizedCPUs | AWS Lambda only. The average number of vCPUs utilized while running user code. |
| recommendedMemory | AWS Lambda only. The recommended memory setting for the function in MB. |

### addAttribute(key, value)

Add a custom attribute to the data return by SAAF. 

### getAttribute(key)

Get an attribute already stored in SAAF.

### addTimeStamp(key, *optional* timeSince)

Add a custom time stamp to SAAF. By default this will store the time in ms from when SAAF started to when this method was called. If a secondary time stamp is supplied the different between the current time and that will be calculated.

### consumeResponse(response)

This function has been deprecated. Instead supply the response object through the overloaded finish method: finish(response). If using a POJO response object, use this method to pull the attributes from the object and add them to SAAF.

# Error Messages

In the event of something going wrong, SAAF will append error messages to the response output.

| **Error** | **Description** |
| --------- | --------------- |
| SAAFContainerError | inspectContainer was called twice. |
| SAAFPlatformError | inspectPlatform was called twice. |
| SAAFLinuxError | inspectLinux was called twice. |
| SAAFCPUDeltaError | inspectCPU was not called before calling inspectCPUDelta |
| SAAFMemoryError | /proc/vmstat does not exist, so page faults could not be collected. |
| SAAFMemoryDeltaError | inspectMemory was not called before calling inspectMemoryDelta, or /proc/vmstat does not exist. |
| SAAFRecommendConfigurationError | A memory setting could not be recommended, for example because inspectCPU or inspectPlatform were not called. |
| SAAFConsumeResponseError | There was an error consuming the response POJO. This can be caused by null values in the Inspector's attributes map. |

&nbsp;
