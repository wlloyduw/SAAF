import json
import logging
import os
import subprocess
import re
import uuid
import shlex
import time

#
# Execute a bash command and get the output.
#
# @param command An array of strings with each part of the command.
# @return Standard out of the command.
#
def runCommand(command):
    return os.popen(command).read()

#
# Global variables that will persist through multiple invocations.
#
invocations = 0
initialization_time = int(round(time.time() * 1000))
ticks_per_second = int(runCommand("getconf CLK_TCK"))

#
# SAAF
#
# @author Wes Lloyd
# @author Wen Shu
# @author Robert Cordingly
#
class Inspector:
    
    #
    # Initialize SAAF.
    #
    # __attributes: Used to store information collected by each function.
    # __startTime:  The time the function started running.
    #
    def __init__(self):
        global invocations
        global initialization_time
        invocations += 1
        
        self.__startTime = int(round(time.time() * 1000))
        self.__attributes = {
            "version": 0.7, 
            "lang": "python", 
            "startTime": self.__startTime,
            "invocations": invocations,
            "initializationTime": initialization_time
        }

        self.__cpuPolls = []
        self.__memoryPolls = []
        self.__networkPolls = []

        self.__inspectedCPU = False
        self.__inspectedCPUDelta = False
        self.__inspectedMemory = False
        self.__inspectedMemoryDelta = False
        self.__inspectedContainer = False
        self.__inspectedContainerDelta = False
        self.__inspectedPlatform = False
        self.__inspectedPlatformDelta = False
        self.__inspectedLinux = False
        self.__inspectedLinuxDelta = False
        
    #
    # Collect information about the runtime container.
    #
    # uuid:            A unique identifier assigned to a container if one does not already exist.
    # newcontainer:    Whether a container is new (no assigned uuid) or if it has been used before.
    #
    def inspectContainer(self):
        self.__inspectedContainer = True

        myUuid = ''
        newContainer = 1
        if os.path.isfile('/tmp/container-id'):
            stampFile = open('/tmp/container-id', 'r')
            stampID = stampFile.readline()
            myUuid = stampID
            stampFile.close()
            newContainer = 0
        else:
            stampFile = open('/tmp/container-id', 'w')
            myUuid = str(uuid.uuid4())
            stampFile.write(myUuid)
            stampFile.close()
            
        self.__attributes['uuid'] = myUuid
        self.__attributes['newcontainer'] = newContainer
        
        
    #
    # Collect information about the CPU assigned to this function.
    #
    # cpuType:     The model name of the CPU.
    # cpuModel:    The model number of the CPU.
    # cpuCores:     The number of vCPUs allocated to the function.
    # cpuInfo:    Detailed information about all aspects of the CPU.
    #
    def inspectCPUInfo(self):
        with open('/proc/cpuinfo', 'r') as file:
            cpuInfo = file.read()
        lines = cpuInfo.split('\n')
        
        cpu_info = {}
        core_list = []
        cpu_count = 0
        for line in lines:
            try:
                keyValue = line.split(':')
                key = keyValue[0].strip().replace(" ", "_")

                if key == 'processor':
                    cpu_count += 1
                elif key == 'power_management' or key == 'CPU_revision':
                    core_list.append(cpu_info)
                    cpu_info = {}
                    continue
                
                value = keyValue[1].strip()
                
                if (key == "flags" or key == "bugs" or key == "Features"):
                    value = value.split(" ")
                
                cpu_info[key] = value
            except Exception as e:
                pass
            
        if 'model_name' in core_list[0]:
            self.__attributes['cpuType'] = core_list[0]['model_name']
            self.__attributes['cpuModel'] = core_list[0]['model']
            self.__attributes['architecture'] = "x86"
        else:
            list_len = len(core_list) - 1
            if 'Model' in core_list[list_len]:
                self.__attributes['cpuModel'] = core_list[list_len]['Model']
            self.__attributes['architecture'] = "arm64"
        self.__attributes['cpuCores'] = int(cpu_count)
        self.__attributes['cpuInfo'] = core_list
        
    #
    # Collect timing CPU metrics
    #
    def pollCPUStats(self):
        global ticks_per_second
        
        timeStamp = int(round(time.time() * 1000))

        cpuValues = ["cpuUser", "cpuNice", "cpuKernel", "cpuIdle", "cpuIOWait", "cpuIrq", "cpuSoftIrq", "cpuSteal", "cpuGuest", "cpuGuestNice"]
        data = {"time": timeStamp}
        
        tick_rate = 1000 / ticks_per_second

        with open('/proc/stat', 'r') as file:
            stats = file.read()
        lines = stats.split('\n')
        lines[0] = lines[0].replace("cpu  ", "cpuTotal ")
        
        for line in lines:
            values = line.split(" ")
            title = values[0].strip()
            
            if ("cpu" in title):
                index = 1
                stats = {}
                for value in cpuValues:
                    stats[value] = int(values[index]) * (tick_rate)
                    index += 1
                data[title] = stats
            else:
                if len(values) >= 2:
                    data[title] = int(values[1])
                    
        self.__cpuPolls.append(data)
        
        
    #
    # Collect information about the CPU assigned to this function.
    #
    # cpuUsr:      Time spent normally executing in user mode.
    # cpuNice:     Time spent executing niced processes in user mode.
    # cpuKrn:      Time spent executing processes in kernel mode.
    # cpuIdle:     Time spent idle.
    # cpuIowait:   Time spent waiting for I/O to complete.
    # cpuIrq:      Time spent servicing interrupts.
    # cpuSoftIrq:  Time spent servicing software interrupts.
    # vmcpusteal:  Time spent waiting for real CPU while hypervisor is using another virtual CPU.
    # contextSwitches: Number of context switches.
    #
    def inspectCPU(self):
        self.__inspectedCPU = True

        self.pollCPUStats()

        CPUMetrics = ["cpuUser", "cpuNice", "cpuKernel", "cpuIdle", "cpuIOWait", "cpuIrq", "cpuSoftIrq", "cpuSteal", "cpuGuest", "cpuGuestNice"]
        for metric in CPUMetrics:
            self.__attributes[metric] = self.__cpuPolls[0]['cpuTotal'][metric]

        self.__attributes['bootTime'] = self.__cpuPolls[0]['btime']
    #
    # Compare information gained from inspectCPU to the current CPU metrics.
    #
    # Note: This function should be called at the end of your function and 
    # must be called AFTER inspectCPU.
    #
    # cpuUsrDelta:      Time spent normally executing in user mode.
    # cpuNiceDelta:     Time spent executing niced processes in user mode.
    # cpuKrnDelta:      Time spent executing processes in kernel mode.
    # cpuIdleDelta:     Time spent idle.
    # cpuIowaitDelta:   Time spent waiting for I/O to complete.
    # cpuIrqDelta:      Time spent servicing interrupts.
    # cpuSoftIrqDelta:  Time spent servicing software interrupts.
    # vmcpustealDelta:  Time spent waiting for real CPU while hypervisor is using another virtual CPU.
    # contextSwitchesDelta: Number of context switches.
    #
    def inspectCPUDelta(self):
        if (self.__inspectedCPU):
            self.__inspectedCPUDelta = True
            
            self.pollCPUStats()
            totalPolls = len(self.__cpuPolls)
            
            CPUMetrics = ["cpuUser", "cpuNice", "cpuKernel", "cpuIdle", "cpuIOWait", "cpuIrq", "cpuSoftIrq", "cpuSteal", "cpuGuest", "cpuGuestNice"]
            CPUTotal = 0
            for metric in CPUMetrics:
                value = self.__cpuPolls[totalPolls - 1]['cpuTotal'][metric]  - self.__cpuPolls[0]['cpuTotal'][metric]
                self.__attributes[metric + "Delta"] = value
                CPUTotal += value
        else:
            self.__attributes['SAAFCPUDeltaError'] = "CPU not inspected before collecting deltas!"

    #
    # Make CPU polls accessible to the function.
    #
    def processCPUPolls(self):
        self.__attributes['cpuPolls'] = self.__cpuPolls

    #
    # Inspects /proc/meminfo and /proc/vmstat. Add memory specific attributes:
    # 
    # totalMemory:     Total memory allocated to the VM in kB.
    # freeMemory:      Current free memory in kB when inspectMemory is called.
    # pageFaults:      Total number of page faults experienced by the vm since boot.
    # majorPageFaults: Total number of major page faults experienced since boot.
    #
    def inspectMemory(self):
        self.__inspectedMemory = True
        memInfo = ""
        with open('/proc/meminfo', 'r') as file:
            memInfo = file.read()
        lines = memInfo.split('\n')
        self.__attributes['totalMemory'] = int(lines[0].replace("MemTotal:", "").replace(" kB", "").strip())
        self.__attributes['freeMemory'] = int(lines[1].replace("MemFree:", "").replace(" kB", "").strip())

        if os.path.isfile('/proc/vmstat'):
            vmStat = ""
            with open('/proc/vmstat', 'r') as file:
                vmStat = file.read()
            lines = vmStat.split("\n")
            for line in lines:
                if 'pgfault' in line:
                    self.__attributes['pageFaults'] = int(line.split(' ')[1])
                elif 'mgmajfault' in line:
                    self.__attributes['majorPageFaults'] = int(line.split(' ')[1])
        else:
            self.__attributes['SAAFMemoryError'] = "/proc/vmstat does not exist!"

    #
    # Inspects /proc/vmstat to see how specific memory stats have changed.
    # 
    # pageFaultsDelta:     The number of page faults experienced since inspectMemory was called.
    # majorPageFaultsDelta: The number of major pafe faults since inspectMemory was called.
    #
    def inspectMemoryDelta(self):
        if (self.__inspectedMemory):
            self.__inspectedMemoryDelta = True
            if os.path.isfile('/proc/vmstat'):
                vmStat = ""
                with open('/proc/vmstat', 'r') as file:
                    vmStat = file.read()
                lines = vmStat.split("\n")
                for line in lines:
                    if 'pgfault' in line:
                        self.__attributes['pageFaultsDelta'] = int(line.split(' ')[1]) - self.__attributes['pageFaults']
                    elif 'mgmajfault' in line:
                        self.__attributes['majorPageFaultsDelta'] = int(line.split(' ')[1]) - self.__attributes['majorPageFaults']
            else:
                self.__attributes['SAAFMemoryDeltaError'] = "/proc/vmstat does not exist!"
        else:
            self.__attributes['SAAFMemoryDeltaError'] = "Memory not inspected before collecting deltas!"
        
    #
    # Collect information about the current FaaS platform.
    #
    # platform:        The FaaS platform hosting this function.
    # containerID:     A unique identifier for containers of a platform.
    # vmID:            A unique identifier for virtual machines of a platform.
    # functionName:    The name of the function.
    # functionMemory:  The memory setting of the function.
    # functionRegion:  The region the function is deployed onto.
    #
    def inspectPlatform(self):
        self.__inspectedPlatform = True

        key = os.environ.get('AWS_LAMBDA_LOG_STREAM_NAME', None)
        if (key != None):
            self.__attributes['platform'] = "AWS Lambda"
            self.__attributes['containerID'] = key
            self.__attributes['functionName'] = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', None)
            self.__attributes['functionMemory'] = os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', None)
            self.__attributes['functionRegion'] = os.environ.get('AWS_REGION', None)

            vmID = runCommand('cat /proc/self/cgroup | grep 2:cpu').replace('\n', '')
            self.__attributes['vmID'] = vmID[20: 26]
        else:
            key = os.environ.get('X_GOOGLE_FUNCTION_NAME', None)
            if (key != None):
                self.__attributes['platform'] = "Google Cloud Functions"
                self.__attributes['functionName'] = key
                self.__attributes['functionMemory'] = os.environ.get('X_GOOGLE_FUNCTION_MEMORY_MB', None)
                self.__attributes['functionRegion'] = os.environ.get('X_GOOGLE_FUNCTION_REGION', None)
            else:
                key = os.environ.get('__OW_ACTION_NAME', None)
                if (key != None):
                    self.__attributes['platform'] = "IBM Cloud Functions"
                    self.__attributes['functionName'] = key
                    self.__attributes['functionRegion'] = os.environ.get('__OW_API_HOST', None)
                    self.__attributes["vmID"] = runCommand("cat /sys/hypervisor/uuid").strip()

                else:
                    key = os.environ.get('CONTAINER_NAME', None)
                    if (key != None):
                        self.__attributes['platform'] = "Azure Functions"
                        self.__attributes['containerID'] = key
                        self.__attributes['functionName'] = os.environ.get('WEBSITE_SITE_NAME', None)
                        self.__attributes['functionRegion'] = os.environ.get('Location', None)
                    else:
                        key = os.environ.get('KUBERNETES_SERVICE_PORT_HTTPS', None)
                        if (key != None):
                            self.__attributes['platform'] = "OpenFaaS EKS"
                            self.__attributes['http_host'] = os.environ.get('Http_Host', None)
                            self.__attributes['http_foward'] = os.environ.get('Http_X_Forwarded_For', None)
                            self.__attributes['http_start_time'] = os.environ.get('Http_X_Start_Time', None)
                            self.__attributes['host_name'] = os.environ.get('HOSTNAME', None)
                        else:
                            self.__attributes['platform'] = "Unknown Platform"
    
    def __recommendConfiguration(self):
        try:
            if (self.__inspectedPlatform and self.__inspectedCPUDelta):
                if self.__attributes['platform'] == "AWS Lambda":
                    availableCPUs = int(self.__attributes['functionMemory']) / 1792
                    self.__attributes['availableCPUs'] = round(availableCPUs, 3)
                    utilizedCPUs = (self.__attributes['cpuUserDelta'] +
                                    self.__attributes['cpuKernelDelta']) / self.__attributes['userRuntime']
                    self.__attributes['utilizedCPUs'] = round(utilizedCPUs, 3)
                    if availableCPUs - utilizedCPUs < 0.1:
                        self.__attributes['recommendedMemory'] = min(max(round(0.000556 * (availableCPUs * 1.1) + 0.012346), 128), 10240)
                    else:
                        self.__attributes['recommendedMemory'] = min(max(round(0.000556 * utilizedCPUs + 0.012346), 128), 10240)
            else:
                self.__attributes['SAAFRecommendConfigurationError'] = "CPU, CPU Delta, and Platform must be inspected before recommending a configuration!"
        except Exception as e:
            self.__attributes['SAAFRecommendConfigurationError'] = "Unable to recommend a configuration. " + str(e)
        
    #
    # Collect information about the linux kernel.
    #
    # linuxVersion:    The version of the linux kernel.
    #
    def inspectLinux(self):
        self.__inspectedLinux = True
        self.__attributes['linuxVersion'] = runCommand('uname -a').replace('\n', '')
        
    #
    # Run all data collection methods and record framework runtime.
    #
    def inspectAll(self):
        self.inspectContainer()
        self.inspectCPUInfo()
        self.inspectPlatform()
        self.inspectLinux()
        self.inspectMemory()
        self.inspectCPU()
        self.addTimeStamp("frameworkRuntime")

    #
    # Run all delta collection methods add userRuntime attribute to further isolate
    # use code runtime from time spent collecting data.
    #
    def inspectAllDeltas(self):

        # Add the 'userRuntime' timestamp.
        if ('frameworkRuntime' in self.__attributes):
            self.addTimeStamp("userRuntime", self.__startTime + self.__attributes['frameworkRuntime'])

        deltaTime = int(round(time.time() * 1000))
        self.inspectCPUDelta()
        self.inspectMemoryDelta()
        self.__recommendConfiguration()
        self.addTimeStamp("frameworkRuntimeDeltas", deltaTime)
        
    #
    # Add a custom attribute to the output.
    #
    # @param key A string ot use as the key value.
    # @param value The value to associate with that key.
    #
    def addAttribute(self, key, value):
        self.__attributes[key] = value
        
    #
    # Gets a custom attribute from the attribute list.
    #
    # @param key The key of the attribute.
    # @return The object associated with the key.
    #
    def getAttribute(self, key):
        return self.__attributes[key]
        
    #
    # Add custom time stamps to the output. The key value determines the name
    # of the attribute and the value will be the time from Inspector initialization
    # to this function call. Add timeSince to compare current time to a different time.
    #
    # @param key The name of the time stamp.
    #
    def addTimeStamp(self, key, timeSince = None):
        if timeSince == None:
            timeSince = self.__startTime
        currentTime = int(round(time.time() * 1000))
        self.__attributes[key] = currentTime - timeSince
        
    #
    # Finalize the Inspector. Calculator the total runtime and return the dictionary
    # object containing all attributes collected.
    #
    # @return Attributes collected by the Inspector.
    #
    def finish(self):
        self.addTimeStamp('runtime')
        self.__attributes['endTime'] = int(round(time.time() * 1000))
        return self.__attributes
