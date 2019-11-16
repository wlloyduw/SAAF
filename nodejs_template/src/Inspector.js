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

class Inspector {
    /**
     * Initialize SAAF.
     *
     * attributes:  Used to store information collected by each function.
     * startTime:   The time the function started running.
     */
    constructor() {
        this.startTime = process.hrtime();
        this.attributes = {"version": 0.4, "lang": "node.js"};

        this.inspectedCPU = false;
        this.inspectedMemory = false;
        this.inspectedContainer = false;
        this.inspectedPlatform = false;
        this.inspectedLinux = false;
    }

    /**
     * Collect information about the runtime container.
     *
     * uuid:            A unique identifier assigned to a container if one does not already exist.
     * newcontainer:    Whether a container is new (no assigned uuid) or if it has been used before.
     * vmuptime:        The time when the system started in Unix time.
     */
    inspectContainer() {
        this.inspectedContainer = true;

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

        this.attributes['uuid'] = myUuid;
        this.attributes['newcontainer'] = newContainer;

        let upTime = this.runCommand('cat /proc/stat | grep btime');
        upTime = upTime.replace('btime ', '').trim();
        this.attributes['vmuptime'] = parseInt(upTime);
    }

    /**
     * Collect information about the CPU assigned to this function.
     *
     * cpuType:     The model name of the CPU.
     * cpuModel:    The model number of the CPU.
     * cpuUsr:      Time spent normally executing in user mode.
     * cpuNice:     Time spent executing niced processes in user mode.
     * cpuKrn:      Time spent executing processes in kernel mode.
     * cpuIdle:     Time spent idle.
     * cpuIowait:   Time spent waiting for I/O to complete.
     * cpuIrq:      Time spent servicing interrupts.
     * cpuSoftIrq:  Time spent servicing software interrupts.
     * vmcpusteal:  Time spent waiting for real CPU while hypervisor is using another virtual CPU.
     * contextSwitches: Number of context switches.
     */
    inspectCPU() {
        this.inspectedCPU = true;

        let command = this.runCommand('grep \'model name\t:\' /proc/cpuinfo | head -1');
        let CPUModelName = command.replace('model name\t:', '').trim();
        this.attributes['cpuType'] = CPUModelName;

        command = this.runCommand('grep \'model\t\t:\' /proc/cpuinfo | head -1');
        let CPUModel = command.replace('model\t\t: ', '').trim();
        this.attributes['cpuModel'] = CPUModel;

        let child = this.runCommand('cat /proc/stat | grep "^cpu" | head -1');
        let CPUMetrics = child.replace('\n', '');
        CPUMetrics = CPUMetrics.replace('cpu  ', '');
        CPUMetrics = CPUMetrics.split(" ");

        let metricsNames = ['cpuUsr', 'cpuNice', 'cpuKrn', 'cpuIdle',
                            'cpuIowait', 'cpuIrq', 'cpuSoftIrq', 'vmcpusteal'];
        for (let i = 0; i < metricsNames.length; i++) {
            this.attributes[metricsNames[i]] = parseInt(CPUMetrics[i]);
        }

        child = this.runCommand('cat /proc/stat | grep "ctxt"');
        let contextSwitches = child.replace('\n','');
        contextSwitches = contextSwitches.replace('ctxt ', '');
        this.attributes['contextSwitches'] = parseInt(contextSwitches);
    }
    
    /**
     * Compare information gained from inspectCPU to the current CPU metrics.
     *
     * cpuUsrDelta:      Time spent normally executing in user mode.
     * cpuNiceDelta:     Time spent executing niced processes in user mode.
     * cpuKrnDelta:      Time spent executing processes in kernel mode.
     * cpuIdleDelta:     Time spent idle.
     * cpuIowaitDelta:   Time spent waiting for I/O to complete.
     * cpuIrqDelta:      Time spent servicing interrupts.
     * cpuSoftIrqDelta:  Time spent servicing software interrupts.
     * vmcpustealDelta:  Time spent waiting for real CPU while hypervisor is using another virtual CPU.
     * contextSwitchesDelta: Number of context switches.
     */
    inspectCPUDelta() {
        if (this.inspectedCPU) {
            let child = this.runCommand('cat /proc/stat | grep "^cpu" | head -1');
            let CPUMetrics = child.replace('\n', '');
            CPUMetrics = CPUMetrics.replace('cpu  ', '');
            CPUMetrics = CPUMetrics.split(" ");

            let metricsNames = ['cpuUsr', 'cpuNice', 'cpuKrn', 'cpuIdle',
                                'cpuIowait', 'cpuIrq', 'cpuSoftIrq', 'vmcpusteal'];
            for (let i = 0; i < metricsNames.length; i++) {
                this.attributes[metricsNames[i] + "Delta"] = parseInt(CPUMetrics[i]) - this.attributes[metricsNames[i]];
            }

            child = this.runCommand('cat /proc/stat | grep "ctxt"');
            let contextSwitches = child.replace('\n','');
            contextSwitches = contextSwitches.replace('\t','');
            contextSwitches = contextSwitches.replace('ctxt ', '');
            this.attributes['contextSwitchesDelta'] = parseInt(contextSwitches) - this.attributes['contextSwitches']
        } else {
            this.attributes["SAAFCPUDeltaError"] = "CPU not inspected before collecting deltas!";
        }
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
        this.inspectedMemory = true;
        var memInfo = fs.readFileSync("/proc/meminfo", "utf8");
        var lines = memInfo.split("\n");
        this.attributes["totalMemory"] = parseInt(lines[0].replace("MemTotal:", "").replace(" kB", "").trim());
        this.attributes["freeMemory"] = parseInt(lines[1].replace("MemFree:", "").replace(" kB", "").trim());
        
        var vmStat = fs.readFileSync("/proc/vmstat", "utf8");
        var lines = vmStat.split("\n");
        lines.forEach((line) => {
            if (line.indexOf("pgfault") != -1) {
                this.attributes["pageFaults"] = parseInt(line.split(" ")[1]);
            } else if (line.indexOf("mgmajfault") != -1) {
                this.attributes["majorPageFaults"] = parseInt(line.split(" ")[1]);
            }
        });
    }

    /**
     * Inspects /proc/vmstat to see how specific memory stats have changed.
     * 
     * pageFaultsDelta:     The number of page faults experienced since inspectMemory was called.
     * majorPageFaultsDelta: The number of major pafe faults since inspectMemory was called.
     */
    inspectMemoryDelta() {
        if (this.inspectedMemory) {
            var vmStat = fs.readFileSync("/proc/vmstat", "utf8");
            var lines = vmStat.split("\n");
            lines.forEach((line) => {
                if (line.indexOf("pgfault") != -1) {
                    this.attributes["pageFaultsDelta"] = parseInt(line.split(" ")[1]) - this.attributes["pageFaults"];
                } else if (line.indexOf("mgmajfault") != -1) {
                    this.attributes["majorPageFaultsDelta"] = parseInt(line.split(" ")[1]) - this.attributes["majorPageFaults"];
                }
            });
        } else {
            this.attributes["SAAFMemoryDeltaError"] = "Memory not inspected before collecting deltas!";
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
        this.inspectedPlatform = true;
        
        var key = process.env.AWS_LAMBDA_LOG_STREAM_NAME;
        if (key != null) {
            this.attributes["platform"] = "AWS Lambda";
            this.attributes["containerID"] = key;
            this.attributes["functionName"] = process.env.AWS_LAMBDA_FUNCTION_NAME;
            this.attributes["functionMemory"] = process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE;
            this.attributes["functionRegion"] = process.env.AWS_REGION;

            var vmID = this.runCommand("cat /proc/self/cgroup");
            var index = vmID.indexOf("sandbox-root");
            this.attributes["vmID"] = vmID.substring(index + 13, index + 19);
        } else {
            key = process.env.X_GOOGLE_FUNCTION_NAME;
            if (key != null) {
                this.attributes["platform"] = "Google Cloud Functions";
                this.attributes["functionName"] = key;
                this.attributes["functionMemory"] = process.env.X_GOOGLE_FUNCTION_MEMORY_MB;
                this.attributes["functionRegion"] = process.env.X_GOOGLE_FUNCTION_REGION;
            } else {
                key = process.env.__OW_ACTION_NAME;
                if (key != null) {
                    this.attributes["platform"] = "IBM Cloud Functions";
                    this.attributes["functionName"] = key;
                    this.attributes["functionRegion"] = process.env.__OW_API_HOST;
                    this.attributes["vmID"] = this.runCommand("cat /sys/hypervisor/uuid").trim();
                } else {
                    key = process.env.CONTAINER_NAME;
                    if (key != null) {
                        this.attributes["platform"] = "Azure Functions";
                        this.attributes["containerID"] = key;
                        this.attributes["functionName"] = process.env.WEBSITE_SITE_NAME;
                        this.attributes["functionRegion"] = process.env.Location;
                    } else {
                        this.attributes["platform"] = "Unknown Platform";
                    }
                }
            }
        }
    }
    
    /**
     * Collect information about the linux kernel.
     *
     * linuxVersion:    The version of the linux kernel.
     */
    inspectLinux() {
        this.inspectedLinux = true;
        this.attributes['linuxVersion'] = this.runCommand('uname -v').replace('\n', '');
    }
    
    /**
     * Run all data collection methods and record framework runtime.
     */
    inspectAll() {
        this.inspectContainer();
        this.inspectPlatform();
        this.inspectLinux();
        this.inspectMemory();
        this.inspectCPU();
        this.addTimeStamp("frameworkRuntime");
    }

    /**
     * Run all delta collection methods add userRuntime attribute to further isolate
     * use code runtime from time spent collecting data.
     */
    inspectAllDeltas() {
        this.inspectCPUDelta();
        this.inspectMemoryDelta();
    }
    
    /**
     * Add a custom attribute to the output.
     *
     * @param key A string to use as the key value.
     * @param value The value to associate with that key.
     */
    addAttribute(key, value) {
        this.attributes[key] = value;
    }
    
    /**
     * Gets a custom attribute from the attribute list.
     * 
     * @param key The key of the attribute.
     * @return The object itself. Cast into appropriate data type.
     */
    getAttribute(key) {
        return this.attributes[key];
    }
    
    /**
     * Add custom time stamps to the output. The key value determines the name
     * of the attribute and the value will be the time from Inspector initialization
     * to this function call. 
     *
     * @param key The name of the time stamp.
     */
    addTimeStamp(key) {
        let timeSinceStart = process.hrtime(this.startTime);
        this.attributes[key] = timeSinceStart[0] * 1000 + Math.round(timeSinceStart[1] / 10000) / 100;
    }

    /**
     * Execute a bash command and get the output.
     *
     * @param command An array of strings with each part of the command.
     * @return Standard out of the command.
     */
    runCommand(command) {
        return execSync(command, { encoding : 'utf8' });
    }

    pushS3(bucket) {
        //return new Promise((resolve, reject) => {
            const aws = require('aws-sdk');
            const s3 = new aws.S3();

            const output = JSON.stringify(this.finish());
            let uuidv4 = require('uuid/v4');
            let runUUID = uuidv4();

            var params = {
                Body: output, 
                Bucket: bucket, 
                Key: "run " + runUUID + ".json"
            };
            s3.putObject(params, (err, data) => {
                if (err) {
                    this.addAttribute("SAAFS3Error", "ERROR PUSHING TO S3 " + err);
                    //context.fail(err);
                } else {
                    this.addAttribute("SAAFS3Error", "SUCCESS PUSHING TO S3 " + data);
                    //context.succeed(output.replace("\"", '"'));
                }
            });
        //});
    }

    /**
     * Finalize FaaS inspector. Calculator the total runtime and return the JSON object
     * containing all attributes collected.
     *
     * @return Attributes collected by FaaS Inspector.
     */
    finish() {
        let endTime = process.hrtime(this.startTime);
        this.attributes['runtime'] = endTime[0] * 1000 + Math.round(endTime[1] / 10000) / 100;
        return this.attributes;
    }
}

module.exports = Inspector;