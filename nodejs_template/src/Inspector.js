/**
 * SAAF
 *
 *
 * @author Wes Lloyd
 * @author Wen Shu
 * @author Robert Cordingly
 */

const { execSync } = require('child_process');
const fs = require('fs');

/**
 * Execute a bash command and get the output.
 *
 * @param command A string containing the command to run.
 * @return Standard out of the command.
 */
function runCommand(command) {
    try {
        return execSync(command, { encoding : 'utf8' });
    } catch (e) {
        return e.stdout || '';
    }
}

/**
 * Global variables that will persist through multiple invocations.
 */
let invocations = 0;
const initializationTime = Date.now();
const ticksPerSecond = parseInt(runCommand("getconf CLK_TCK")) || 100;

/**
 * CPU metrics reported by /proc/stat, in the order they appear.
 */
const cpuMetrics = ["cpuUser", "cpuNice", "cpuKernel", "cpuIdle", "cpuIOWait",
                    "cpuIrq", "cpuSoftIrq", "cpuSteal", "cpuGuest", "cpuGuestNice"];

class Inspector {

    #attributes;
    #startTime;
    #cpuPolls;

    #inspectedCPU;
    #inspectedCPUDelta;
    #inspectedMemory;
    #inspectedMemoryDelta;
    #inspectedContainer;
    #inspectedPlatform;
    #inspectedLinux;
    #inspectedEnvironment;

    /**
     * Initialize SAAF.
     *
     * attributes:  Used to store information collected by each function.
     * startTime:   The time the function started running.
     */
    constructor() {
        invocations += 1;

        this.#startTime = Date.now();
        this.#attributes = {
            "version": 0.8,
            "lang": "node.js",
            "startTime": this.#startTime,
            "invocations": invocations,
            "initializationTime": initializationTime
        };

        this.#cpuPolls = [];

        this.#inspectedCPU = false;
        this.#inspectedCPUDelta = false;
        this.#inspectedMemory = false;
        this.#inspectedMemoryDelta = false;
        this.#inspectedContainer = false;
        this.#inspectedPlatform = false;
        this.#inspectedLinux = false;
        this.#inspectedEnvironment = false;
    }

    /**
     * Collect information about the runtime container.
     *
     * uuid:            A unique identifier assigned to a container if one does not already exist.
     * newcontainer:    Whether a container is new (no assigned uuid) or if it has been used before.
     */
    inspectContainer() {
        this.#inspectedContainer = true;

        let myUuid = '';
        let newContainer = 1;
        if (fs.existsSync('/tmp/container-id')) {
            myUuid = fs.readFileSync('/tmp/container-id', { encoding : 'utf8' });
            newContainer = 0;
        } else {
            let uuidv4 = require('uuid/v4');
            myUuid = uuidv4();
            fs.writeFileSync('/tmp/container-id', myUuid);
        }

        this.#attributes['uuid'] = myUuid;
        this.#attributes['newcontainer'] = newContainer;
    }

    /**
     * Collect information about the CPU assigned to this function.
     *
     * cpuType:         The model name of the CPU.
     * cpuModel:        The model number of the CPU.
     * architecture:    The architecture of the CPU (x86 or arm64).
     * cpuCores:        The number of vCPUs allocated to the function.
     * cpuInfo:         A list containing the details of only the first vCPU, without the
     *                  flags, bugs, and Features lists.
     *
     * Note: Use inspectCPUInfoVerbose to collect the details of every vCPU.
     */
    inspectCPUInfo() {
        this.#inspectCPUInfo(false);
    }

    /**
     * Collect the same information as inspectCPUInfo, except cpuInfo contains
     * every detail of every vCPU, including the flags, bugs, and Features lists.
     */
    inspectCPUInfoVerbose() {
        this.#inspectCPUInfo(true);
    }

    /**
     * Parse /proc/cpuinfo and add the CPU info attributes.
     *
     * @param verbose Whether to include the details of every vCPU in cpuInfo.
     */
    #inspectCPUInfo(verbose) {
        let cpuInfo = fs.readFileSync('/proc/cpuinfo', 'utf8');
        let lines = cpuInfo.split('\n');

        let coreInfo = {};
        let coreList = [];
        let cpuCount = 0;
        for (let line of lines) {
            try {
                let keyValue = line.split(':');
                let key = keyValue[0].trim().replace(/ /g, '_');

                if (key == 'processor') {
                    cpuCount += 1;
                } else if (key == 'power_management' || key == 'CPU_revision') {
                    coreList.push(coreInfo);
                    coreInfo = {};
                    continue;
                }

                let value = keyValue[1].trim();

                if (key == "flags" || key == "bugs" || key == "Features") {
                    if (!verbose) {
                        continue;
                    }
                    value = value.split(" ");
                }

                coreInfo[key] = value;
            } catch (e) {
            }
        }

        if ('model_name' in coreList[0]) {
            this.#attributes['cpuType'] = coreList[0]['model_name'];
            this.#attributes['cpuModel'] = coreList[0]['model'];
            this.#attributes['architecture'] = "x86";
        } else {
            let listLen = coreList.length - 1;
            if ('Model' in coreList[listLen]) {
                this.#attributes['cpuModel'] = coreList[listLen]['Model'];
            }
            this.#attributes['architecture'] = "arm64";
        }
        this.#attributes['cpuCores'] = cpuCount;
        this.#attributes['cpuInfo'] = verbose ? coreList : coreList.slice(0, 1);
    }

    /**
     * Collect timing CPU metrics. Each call records a poll of /proc/stat
     * with all CPU times converted from ticks into milliseconds.
     */
    pollCPUStats() {
        let timeStamp = Date.now();

        let data = {"time": timeStamp};

        let tickRate = 1000 / ticksPerSecond;

        let stats = fs.readFileSync('/proc/stat', 'utf8');
        let lines = stats.split('\n');
        lines[0] = lines[0].replace("cpu  ", "cpuTotal ");

        for (let line of lines) {
            let values = line.split(" ");
            let title = values[0].trim();

            if (title.includes("cpu")) {
                let cpuStats = {};
                for (let i = 0; i < cpuMetrics.length; i++) {
                    cpuStats[cpuMetrics[i]] = parseInt(values[i + 1]) * tickRate;
                }
                data[title] = cpuStats;
            } else if (values.length >= 2) {
                data[title] = parseInt(values[1]);
            }
        }

        this.#cpuPolls.push(data);
    }

    /**
     * Collect information about the CPU assigned to this function.
     *
     * cpuUser:         Time spent normally executing in user mode.
     * cpuNice:         Time spent executing niced processes in user mode.
     * cpuKernel:       Time spent executing processes in kernel mode.
     * cpuIdle:         Time spent idle.
     * cpuIOWait:       Time spent waiting for I/O to complete.
     * cpuIrq:          Time spent servicing interrupts.
     * cpuSoftIrq:      Time spent servicing software interrupts.
     * cpuSteal:        Time spent waiting for real CPU while hypervisor is using another virtual CPU.
     * cpuGuest:        Time spent running a virtual CPU for guest operating systems.
     * cpuGuestNice:    Time spent running a niced guest.
     * bootTime:        Time when the host booted in seconds since the Unix epoch.
     */
    inspectCPU() {
        this.#inspectedCPU = true;

        this.pollCPUStats();

        for (let metric of cpuMetrics) {
            this.#attributes[metric] = this.#cpuPolls[0]['cpuTotal'][metric];
        }

        this.#attributes['bootTime'] = this.#cpuPolls[0]['btime'];
    }

    /**
     * Compare information gained from inspectCPU to the current CPU metrics.
     *
     * Note: This function should be called at the end of your function and
     * must be called AFTER inspectCPU.
     *
     * cpuUserDelta:        Time spent normally executing in user mode.
     * cpuNiceDelta:        Time spent executing niced processes in user mode.
     * cpuKernelDelta:      Time spent executing processes in kernel mode.
     * cpuIdleDelta:        Time spent idle.
     * cpuIOWaitDelta:      Time spent waiting for I/O to complete.
     * cpuIrqDelta:         Time spent servicing interrupts.
     * cpuSoftIrqDelta:     Time spent servicing software interrupts.
     * cpuStealDelta:       Time spent waiting for real CPU while hypervisor is using another virtual CPU.
     * cpuGuestDelta:       Time spent running a virtual CPU for guest operating systems.
     * cpuGuestNiceDelta:   Time spent running a niced guest.
     */
    inspectCPUDelta() {
        if (this.#inspectedCPU) {
            this.#inspectedCPUDelta = true;

            this.pollCPUStats();
            let totalPolls = this.#cpuPolls.length;

            for (let metric of cpuMetrics) {
                this.#attributes[metric + "Delta"] = this.#cpuPolls[totalPolls - 1]['cpuTotal'][metric] - this.#cpuPolls[0]['cpuTotal'][metric];
            }
        } else {
            this.#attributes['SAAFCPUDeltaError'] = "CPU not inspected before collecting deltas!";
        }
    }

    /**
     * Make CPU polls accessible to the function.
     */
    processCPUPolls() {
        this.#attributes['cpuPolls'] = this.#cpuPolls;
    }

    /**
     * Inspects /proc/meminfo and /proc/vmstat. Add memory specific attributes:
     *
     * totalMemory:     Total memory allocated to the VM in kB.
     * freeMemory:      Current free memory in kB when inspectMemory is called.
     * pageFaults:      Total number of page faults experienced by the vm since boot.
     * majorPageFaults: Total number of major page faults experienced since boot.
     */
    inspectMemory() {
        this.#inspectedMemory = true;
        let memInfo = fs.readFileSync('/proc/meminfo', 'utf8');
        let lines = memInfo.split('\n');
        this.#attributes['totalMemory'] = parseInt(lines[0].replace("MemTotal:", "").replace(" kB", "").trim());
        this.#attributes['freeMemory'] = parseInt(lines[1].replace("MemFree:", "").replace(" kB", "").trim());

        if (fs.existsSync('/proc/vmstat')) {
            let vmStat = fs.readFileSync('/proc/vmstat', 'utf8');
            lines = vmStat.split('\n');
            for (let line of lines) {
                if (line.includes('pgfault')) {
                    this.#attributes['pageFaults'] = parseInt(line.split(' ')[1]);
                } else if (line.includes('pgmajfault')) {
                    this.#attributes['majorPageFaults'] = parseInt(line.split(' ')[1]);
                }
            }
        } else {
            this.#attributes['SAAFMemoryError'] = "/proc/vmstat does not exist!";
        }
    }

    /**
     * Inspects /proc/vmstat to see how specific memory stats have changed.
     *
     * pageFaultsDelta:     The number of page faults experienced since inspectMemory was called.
     * majorPageFaultsDelta: The number of major pafe faults since inspectMemory was called.
     */
    inspectMemoryDelta() {
        if (this.#inspectedMemory) {
            this.#inspectedMemoryDelta = true;
            if (fs.existsSync('/proc/vmstat')) {
                let vmStat = fs.readFileSync('/proc/vmstat', 'utf8');
                let lines = vmStat.split('\n');
                for (let line of lines) {
                    if (line.includes('pgfault')) {
                        this.#attributes['pageFaultsDelta'] = parseInt(line.split(' ')[1]) - this.#attributes['pageFaults'];
                    } else if (line.includes('pgmajfault')) {
                        this.#attributes['majorPageFaultsDelta'] = parseInt(line.split(' ')[1]) - this.#attributes['majorPageFaults'];
                    }
                }
            } else {
                this.#attributes['SAAFMemoryDeltaError'] = "/proc/vmstat does not exist!";
            }
        } else {
            this.#attributes['SAAFMemoryDeltaError'] = "Memory not inspected before collecting deltas!";
        }
    }

    /**
     * Collect information about the current FaaS platform.
     *
     * platform:        The FaaS platform hosting this function.
     * containerID:     A unique identifier for containers of a platform.
     * vmID:            A unique identifier for virtual machines of a platform.
     * functionName:    The name of the function.
     * functionMemory:  The memory setting of the function.
     * functionRegion:  The region the function is deployed onto.
     */
    inspectPlatform() {
        this.#inspectedPlatform = true;

        let key = process.env.AWS_LAMBDA_LOG_STREAM_NAME;
        if (key != null) {
            this.#attributes['platform'] = "AWS Lambda";
            this.#attributes['containerID'] = key;
            this.#attributes['functionName'] = process.env.AWS_LAMBDA_FUNCTION_NAME;
            this.#attributes['functionMemory'] = process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE;
            this.#attributes['functionRegion'] = process.env.AWS_REGION;

            let vmID = runCommand('cat /proc/self/cgroup | grep 2:cpu').replace(/\n/g, '');
            this.#attributes['vmID'] = vmID.substring(20, 26);
        } else {
            key = process.env.X_GOOGLE_FUNCTION_NAME;
            if (key != null) {
                this.#attributes['platform'] = "Google Cloud Functions";
                this.#attributes['functionName'] = key;
                this.#attributes['functionMemory'] = process.env.X_GOOGLE_FUNCTION_MEMORY_MB;
                this.#attributes['functionRegion'] = process.env.X_GOOGLE_FUNCTION_REGION;
            } else {
                key = process.env.__OW_ACTION_NAME;
                if (key != null) {
                    this.#attributes['platform'] = "IBM Cloud Functions";
                    this.#attributes['functionName'] = key;
                    this.#attributes['functionRegion'] = process.env.__OW_API_HOST;
                    this.#attributes['vmID'] = runCommand("cat /sys/hypervisor/uuid").trim();
                } else {
                    key = process.env.CONTAINER_NAME;
                    if (key != null) {
                        this.#attributes['platform'] = "Azure Functions";
                        this.#attributes['containerID'] = key;
                        this.#attributes['functionName'] = process.env.WEBSITE_SITE_NAME;
                        this.#attributes['functionRegion'] = process.env.Location;
                    } else {
                        key = process.env.KUBERNETES_SERVICE_PORT_HTTPS;
                        if (key != null) {
                            this.#attributes['platform'] = "OpenFaaS EKS";
                            this.#attributes['http_host'] = process.env.Http_Host;
                            this.#attributes['http_foward'] = process.env.Http_X_Forwarded_For;
                            this.#attributes['http_start_time'] = process.env.Http_X_Start_Time;
                            this.#attributes['host_name'] = process.env.HOSTNAME;
                        } else {
                            this.#attributes['platform'] = "Unknown Platform";
                        }
                    }
                }
            }
        }
    }

    /**
     * Estimate the CPU utilization of the function and recommend a memory setting.
     * Requires inspectPlatform, inspectCPU, and inspectCPUDelta. Currently only
     * supports AWS Lambda.
     *
     * availableCPUs:       The number of vCPUs available at the current memory setting.
     * utilizedCPUs:        The number of vCPUs utilized while running user code.
     * recommendedMemory:   The recommended memory setting for the function.
     */
    #recommendConfiguration() {
        try {
            if (this.#inspectedPlatform && this.#inspectedCPUDelta) {
                if (this.#attributes['platform'] == "AWS Lambda") {
                    let userRuntime = this.#attributes['userRuntime'];
                    if (!userRuntime) {
                        throw new Error("userRuntime must be greater than zero.");
                    }

                    let availableCPUs = parseInt(this.#attributes['functionMemory']) / 1792;
                    this.#attributes['availableCPUs'] = Math.round(availableCPUs * 1000) / 1000;
                    let utilizedCPUs = (this.#attributes['cpuUserDelta'] +
                                        this.#attributes['cpuKernelDelta']) / userRuntime;
                    this.#attributes['utilizedCPUs'] = Math.round(utilizedCPUs * 1000) / 1000;
                    if (availableCPUs - utilizedCPUs < 0.1) {
                        this.#attributes['recommendedMemory'] = Math.min(Math.max(Math.round(0.000556 * (availableCPUs * 1.1) + 0.012346), 128), 10240);
                    } else {
                        this.#attributes['recommendedMemory'] = Math.min(Math.max(Math.round(0.000556 * utilizedCPUs + 0.012346), 128), 10240);
                    }
                }
            } else {
                this.#attributes['SAAFRecommendConfigurationError'] = "CPU, CPU Delta, and Platform must be inspected before recommending a configuration!";
            }
        } catch (e) {
            this.#attributes['SAAFRecommendConfigurationError'] = "Unable to recommend a configuration. " + e.message;
        }
    }

    /**
     * Collect information about the linux kernel.
     *
     * linuxVersion:    The version of the linux kernel.
     */
    inspectLinux() {
        this.#inspectedLinux = true;
        this.#attributes['linuxVersion'] = runCommand('uname -a').replace(/\n/g, '');
    }

    /**
     * Collect all environment variables. Each variable is added as an attribute
     * using the variable's name as the key.
     *
     * Note: This is not called by inspectAll. Environment variables may contain
     * secrets, such as the temporary AWS credentials provided by AWS Lambda.
     */
    inspectEnvironment() {
        this.#inspectedEnvironment = true;
        for (let [key, value] of Object.entries(process.env)) {
            this.#attributes[key] = value;
        }
    }

    /**
     * Run all data collection methods and record framework runtime.
     */
    inspectAll() {
        this.inspectContainer();
        this.inspectCPUInfo();
        this.inspectPlatform();
        this.inspectLinux();
        this.inspectMemory();
        this.inspectCPU();
        this.addTimeStamp('frameworkRuntime');
    }

    /**
     * Run all delta collection methods add userRuntime attribute to further isolate
     * use code runtime from time spent collecting data.
     */
    inspectAllDeltas() {

        // Add the 'userRuntime' timestamp.
        if ('frameworkRuntime' in this.#attributes) {
            this.addTimeStamp('userRuntime', this.#startTime + this.#attributes['frameworkRuntime']);
        }

        let deltaTime = Date.now();
        this.inspectCPUDelta();
        this.inspectMemoryDelta();
        this.#recommendConfiguration();
        this.addTimeStamp('frameworkRuntimeDeltas', deltaTime);
    }

    /**
     * Add a custom attribute to the output.
     *
     * @param key A string to use as the key value.
     * @param value The value to associate with that key.
     */
    addAttribute(key, value) {
        this.#attributes[key] = value;
    }

    /**
     * Gets a custom attribute from the attribute list.
     *
     * @param key The key of the attribute.
     * @return The object associated with the key.
     */
    getAttribute(key) {
        return this.#attributes[key];
    }

    /**
     * Add custom time stamps to the output. The key value determines the name
     * of the attribute and the value will be the time from Inspector initialization
     * to this function call. Add timeSince to compare current time to a different time.
     *
     * @param key The name of the time stamp.
     * @param timeSince Optional time in ms to compare the current time to.
     */
    addTimeStamp(key, timeSince = null) {
        if (timeSince == null) {
            timeSince = this.#startTime;
        }
        let currentTime = Date.now();
        this.#attributes[key] = currentTime - timeSince;
    }

    /**
     * Finalize the Inspector. Calculate the total runtime and return the JSON object
     * containing all attributes collected.
     *
     * @return Attributes collected by the Inspector.
     */
    finish() {
        this.addTimeStamp('runtime');
        this.#attributes['endTime'] = Date.now();
        return this.#attributes;
    }
}

module.exports = Inspector;
