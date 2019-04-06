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
     * Collect information about the current FaaS platform.
     *
     * platform:    The FaaS platform hosting this function.
     */
    inspectPlatform() {
        const { execSync } = require('child_process');
        let environment = execSync('env', { encoding : 'utf8' });
        if (environment.indexOf("AWS_LAMBDA") > -1) {
            this.attributes['platform'] = "AWS Lambda";
            return 0;
        }
        if (environment.indexOf("X_GOOGLE") > -1) {
            this.attributes['platform'] = "Google Cloud Functions";
            return 0;
        }
        if (environment.indexOf("functions.cloud") > -1) {
            this.attributes['platform'] = "IBM Cloud Functions";
            return 0;
        }
        if (environment.indexOf("microsoft.com/azure-functions") > -1) {
            this.attributes['platform'] = "Azure Functions";
            return 0;
        }
        this.attributes['platform'] = "Unknown Platform";

    }
    
    /**
     * Collect information about the linux kernel.
     *
     * linuxVersion:    The version of the linux kernel.
     */
    inspectLinux() {
        const { execSync } = require('child_process');
        let child = execSync('uname -v', { encoding : 'utf8' });
        let linuxVersion = child.replace('\n', '');
        this.attributes['linuxVersion'] = linuxVersion;
    }

    /**
     * Finalize FaaS inspector. Calculator the total runtime and return the JSON object
     * containing all attributes collected.
     *
     * @returns Attributes collected by FaaS Inspector.
     */
    finish() {
        let endTime = process.hrtime(this.startTime);
        this.attributes['runtime'] = endTime[0] * 1000 + Math.round(endTime[1] / 10000) / 100;
        return this.attributes;
    }
}

module.exports = Inspector;