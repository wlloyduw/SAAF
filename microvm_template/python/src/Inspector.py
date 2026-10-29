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
# @param command A string containing the command to run. It runs in a shell,
#                so it may use pipes.
# @return Standard out of the command.
#
def runCommand(command):
    return subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True).stdout

#
# Global variables that will persist through multiple invocations.
#
invocations = 0
initialization_time = int(round(time.time() * 1000))
ticks_per_second = int(runCommand("getconf CLK_TCK"))

#
# SAAF
#
# The python_template Inspector with changes for AWS Lambda MicroVMs:
# inspectPlatform only reports MicroVM values, and recommendConfiguration is
# removed because its memory model does not apply to MicroVMs.
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
            "version": 0.8, 
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
        self.__inspectedEnvironment = False
        
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
    # cpuType:      The model name of the CPU.
    # cpuModel:     The model number of the CPU.
    # architecture: The architecture of the CPU (x86 or arm64).
    # cpuCores:     The number of vCPUs allocated to the function.
    # cpuInfo:      A list containing the details of only the first vCPU, without the
    #               flags, vmx_flags, bugs, and Features lists.
    #
    # Note: Use inspectCPUInfoVerbose to collect the details of every vCPU.
    #
    def inspectCPUInfo(self):
        self.__inspectCPUInfo(False)

    #
    # Collect the same information as inspectCPUInfo, except cpuInfo contains
    # every detail of every vCPU, including the flags, vmx_flags, bugs, and Features lists.
    #
    def inspectCPUInfoVerbose(self):
        self.__inspectCPUInfo(True)

    #
    # Parse /proc/cpuinfo and add the CPU info attributes.
    #
    # @param verbose Whether to include the details of every vCPU in cpuInfo.
    #
    def __inspectCPUInfo(self, verbose):
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

                if not verbose and key in ("flags", "vmx_flags", "bugs", "Features"):
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
        self.__attributes['cpuInfo'] = core_list if verbose else core_list[:1]
        
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
                elif 'pgmajfault' in line:
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
                    elif 'pgmajfault' in line:
                        self.__attributes['majorPageFaultsDelta'] = int(line.split(' ')[1]) - self.__attributes['majorPageFaults']
            else:
                self.__attributes['SAAFMemoryDeltaError'] = "/proc/vmstat does not exist!"
        else:
            self.__attributes['SAAFMemoryDeltaError'] = "Memory not inspected before collecting deltas!"
        
    #
    # Collect information about the AWS Lambda MicroVM.
    #
    # The image name, memory, and Region come from SAAF_FUNCTION_NAME,
    # SAAF_FUNCTION_MEMORY, and SAAF_FUNCTION_REGION, which publish.sh sets on the
    # image. The MicroVM ID comes from /tmp/microvm-id, which the server writes when
    # Lambda calls the /run hook after the MicroVM starts.
    #
    # platform:        Always "AWS Lambda MicroVM".
    # containerID:     The MicroVM ID.
    # functionName:    The name of the MicroVM image.
    # functionMemory:  The baseline memory of the MicroVM in MB.
    # functionRegion:  The region the MicroVM runs in.
    #
    def inspectPlatform(self):
        self.__inspectedPlatform = True

        self.__attributes['platform'] = "AWS Lambda MicroVM"
        if os.path.isfile('/tmp/microvm-id'):
            with open('/tmp/microvm-id', 'r') as file:
                self.__attributes['containerID'] = file.read().strip()
        self.__attributes['functionName'] = os.environ.get('SAAF_FUNCTION_NAME', None)
        self.__attributes['functionMemory'] = os.environ.get('SAAF_FUNCTION_MEMORY', None)
        self.__attributes['functionRegion'] = os.environ.get('SAAF_FUNCTION_REGION', None)

    #
    # Collect information about the linux kernel.
    #
    # linuxVersion:    The version of the linux kernel.
    #
    def inspectLinux(self):
        self.__inspectedLinux = True
        self.__attributes['linuxVersion'] = runCommand('uname -a').replace('\n', '')
        
    #
    # Collect all environment variables. Each variable is added as an attribute
    # using the variable's name as the key.
    #
    # Note: This is not called by inspectAll. Environment variables may contain
    # secrets, such as the temporary AWS credentials provided by AWS Lambda.
    #
    def inspectEnvironment(self):
        self.__inspectedEnvironment = True
        for key, value in os.environ.items():
            self.__attributes[key] = value
        
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
