/**
 * FaaS Inspector
 *
 *
 * @author Wes Lloyd
 * @author Wen Shu
 * @author Robert Cordingly
 */
class Inspector {

    /**
     * Initialize FaaS Inspector.
     *
     * attributes: Used to store information collected by each function.
     */
    constructor() {
        this.startTime = process.hrtime();
        this.attributes = {"version": 0.2, "lang": "node.js"};
    }

    /**
     * Collect information about the runtime container.
     *
     * uuid:            A unique identifier assigned to a container if one does not already exist.
     * newcontainer:    Whether a container is new (no assigned uuid) or if it has been used before.
     * vmuptime:        The time when the system started in Unix time.
     */
    inspectContainer() {
        let fs = require('fs');
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

        const { spawnSync } = require('child_process');
        const child = spawnSync('grep', ['btime', '/proc/stat'], { encoding : 'utf8' });
        let upTime = child.stdout;
        upTime = upTime.replace('btime ', '');
        upTime = upTime.trim();
        upTime = parseInt(upTime);
        this.attributes['vmuptime'] = upTime;
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
     */
    inspectCPU() {
        const { execSync } = require('child_process');
        let child = execSync('grep \'model name\' /proc/cpuinfo | head -1', { encoding : 'utf8' });
        let CPUModelName = child.replace('\n','');
        CPUModelName = CPUModelName.replace('\t','');
        CPUModelName = CPUModelName.replace('model name: ', '');
        this.attributes['cpuType'] = CPUModelName;

        child = execSync('grep \'model\' /proc/cpuinfo | head -1', { encoding : 'utf8' });
        let CPUModel = child.replace('\n', '');
        CPUModel = CPUModel.replace('\t', '');
        CPUModel = CPUModel.replace('model\t: ', '');
        this.attributes['cpuModel'] = CPUModel;

        child = execSync('cat /proc/stat | grep "^cpu" | head -1', { encoding : 'utf8' });
        let CPUMetrics = child.replace('\n', '');
        CPUMetrics = CPUMetrics.replace('cpu  ', '');
        CPUMetrics = CPUMetrics.split(" ");

        let metricsNames = ['cpuUsr', 'cpuNice', 'cpuKrn', 'cpuIdle',
                            'cpuIowait', 'cpuIrq', 'cpuSoftIrq', 'vmcpusteal'];
        for (let i = 0; i < metricsNames.length; i++) {
            this.attributes[metricsNames[i]] = parseInt(CPUMetrics[i]);
        }
    }
    
    /**
     * Compare information gained from inspectCPU to the current CPU metrics.
     *
     * Note: This function should be called at the end of your function and 
     * must be called AFTER inspectCPU.
     *
     * cpuUsrDelta:      Time spent normally executing in user mode.
     * cpuNiceDelta:     Time spent executing niced processes in user mode.
     * cpuKrnDelta:      Time spent executing processes in kernel mode.
     * cpuIdleDelta:     Time spent idle.
     * cpuIowaitDelta:   Time spent waiting for I/O to complete.
     * cpuIrqDelta:      Time spent servicing interrupts.
     * cpuSoftIrqDelta:  Time spent servicing software interrupts.
     * vmcpustealDelta:  Time spent waiting for real CPU while hypervisor is using another virtual CPU.
     */
    inspectCPUDelta() {
        const { execSync } = require('child_process');
        let child = execSync('cat /proc/stat | grep "^cpu" | head -1', { encoding : 'utf8' });
        let CPUMetrics = child.replace('\n', '');
        CPUMetrics = CPUMetrics.replace('cpu  ', '');
        CPUMetrics = CPUMetrics.split(" ");

        let metricsNames = ['cpuUsr', 'cpuNice', 'cpuKrn', 'cpuIdle',
                            'cpuIowait', 'cpuIrq', 'cpuSoftIrq', 'vmcpusteal'];
        for (let i = 0; i < metricsNames.length; i++) {
            this.attributes[metricsNames[i] + "Delta"] = parseInt(CPUMetrics[i]) - this.attributes[metricsNames[i]]
        }
    }

    /**
     * Collect information about the current FaaS platform.
     *
     * platform:    The FaaS platform hosting this function.
     */
    inspectPlatform() {
        const { execSync } = require('child_process');
        let environment = execSync('env', { encoding : 'utf8' });
        if (environment.indexOf("AWS_LAMBDA") > -1) {
            this.attributes['platform'] = "AWS Lambda";
        } else if (environment.indexOf("X_GOOGLE") > -1) {
            this.attributes['platform'] = "Google Cloud Functions";
        } else if (environment.indexOf("functions.cloud.ibm") > -1) {
            this.attributes['platform'] = "IBM Cloud Functions";
        } else if (environment.indexOf("microsoft.com/azure-functions") > -1) {
            this.attributes['platform'] = "Azure Functions";
        } else {
            this.attributes['platform'] = "Unknown Platform";
        }
    }
    
    /**
     * Collect information about the linux kernel.
     *
     * linuxVersion:    The version of the linux kernel.
     * hostname:        The host name of the system.
     */
    inspectLinux() {
        const { execSync } = require('child_process');
        let child = execSync('uname -v', { encoding : 'utf8' });
        let linuxVersion = child.replace('\n', '');
        this.attributes['linuxVersion'] = linuxVersion;
        
        let call = execSync('hostname', { encoding : 'utf8' });
        let hostname = call.replace('\n', '');
        this.attributes['hostname'] = hostname;
    }
    
    /**
     * Run all data collection methods and record framework runtime.
     */
    inspectAll() {
        this.inspectCPU();
        this.inspectContainer();
        this.inspectLinux();
        this.inspectPlatform();
        this.addTimeStamp("frameworkRuntime");
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