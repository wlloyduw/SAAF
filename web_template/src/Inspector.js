/**
 * SAAF Inspector for AWS Lambda Web Functions.
 *
 * Collection methods match nodejs_template/src/Inspector.js so experiment
 * fields stay comparable. Process-lifetime counters match juypter_template/SAAF.py
 * because one Web Function environment serves many requests.
 *
 * @author Wes Lloyd
 * @author Wen Shu
 * @author Robert Cordingly
 */

const { execSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');

const CONTAINER_ID_PATH = '/tmp/container-id';
const CPU_METRICS = ['cpuUsr', 'cpuNice', 'cpuKrn', 'cpuIdle', 'cpuIowait', 'cpuIrq', 'cpuSoftIrq', 'vmcpusteal'];

let invocations = 0;
let inFlight = 0;
const initializationTime = Date.now();

function cpuSample(statText) {
    const lines = statText.split('\n');
    const cpuLine = lines.find((line) => /^cpu\s+/.test(line));
    if (!cpuLine) {
        return null;
    }

    const values = cpuLine.trim().split(/\s+/).slice(1).map((value) => parseInt(value, 10));
    const sample = {};
    CPU_METRICS.forEach((name, index) => {
        if (Number.isFinite(values[index])) {
            sample[name] = values[index];
        }
    });

    const ctxt = lines.find((line) => line.startsWith('ctxt'));
    if (ctxt) {
        const switches = parseInt(ctxt.trim().split(/\s+/)[1], 10);
        if (Number.isFinite(switches)) {
            sample.contextSwitches = switches;
        }
    }

    const btime = lines.find((line) => line.startsWith('btime'));
    if (btime) {
        const boot = parseInt(btime.trim().split(/\s+/)[1], 10);
        if (Number.isFinite(boot)) {
            sample.vmuptime = boot;
        }
    }

    return sample;
}

class Inspector {
    /**
     * Initialize SAAF.
     *
     * attributes:          Information collected for this request.
     * startTime:           Unix epoch in ms when this request's Inspector was created.
     * invocations:         Requests that have constructed an Inspector in this process.
     * initializationTime:  Unix epoch in ms when this process first loaded SAAF.
     * inFlightRequests:    Inspectors opened and not yet closed, including this one.
     */
    constructor() {
        this.startTime = Date.now();
        invocations += 1;
        inFlight += 1;
        this._open = true;

        this.attributes = {
            version: 0.8,
            lang: 'node.js',
            startTime: this.startTime,
            invocations: invocations,
            initializationTime: initializationTime,
            inFlightRequests: inFlight
        };

        this.inspectedCPU = false;
        this.inspectedMemory = false;
        this.inspectedContainer = false;
        this.inspectedPlatform = false;
        this.inspectedLinux = false;
        this.cpuSample = null;
    }

    /**
     * Collect information about the runtime environment.
     *
     * uuid:            Identifier persisted at /tmp/container-id for this environment.
     * newcontainer:    1 the first time this environment is seen, otherwise 0.
     * vmuptime:        Boot time of the host in seconds since the Unix epoch.
     */
    inspectContainer() {
        this.inspectedContainer = true;

        let myUuid = '';
        let newContainer = 1;
        try {
            if (fs.existsSync(CONTAINER_ID_PATH)) {
                myUuid = fs.readFileSync(CONTAINER_ID_PATH, { encoding: 'utf8' }).trim();
                newContainer = 0;
            } else {
                myUuid = crypto.randomUUID();
                fs.writeFileSync(CONTAINER_ID_PATH, myUuid);
            }
        } catch (err) {
            myUuid = myUuid || crypto.randomUUID();
            this.attributes.SAAFContainerError = 'Unable to persist container id: ' + err.message;
        }

        this.attributes.uuid = myUuid;
        this.attributes.newcontainer = newContainer;

        const stat = this.readText('/proc/stat');
        const sample = stat ? cpuSample(stat) : null;
        if (sample && sample.vmuptime != null) {
            this.attributes.vmuptime = sample.vmuptime;
        }
    }

    /**
     * Collect information about the CPU assigned to this environment.
     *
     * Values are cumulative counters from /proc/stat, in clock ticks.
     * On a Web Function these counters cover the whole environment, so a
     * delta includes CPU used by other requests that overlap this one.
     */
    inspectCPU() {
        const info = this.readText('/proc/cpuinfo');
        const stat = this.readText('/proc/stat');
        const sample = stat ? cpuSample(stat) : null;

        if (!info && !sample) {
            this.attributes.SAAFCPUError = '/proc/cpuinfo and /proc/stat are not available';
            return;
        }

        this.inspectedCPU = true;

        if (info) {
            const modelName = info.match(/^model name\s*:\s*(.+)$/m);
            const hardware = info.match(/^Hardware\s*:\s*(.+)$/m);
            const model = info.match(/^model\s*:\s*(.+)$/m);
            const processors = info.match(/^processor\s*:/gm);
            if (modelName) {
                this.attributes.cpuType = modelName[1].trim();
            } else if (hardware) {
                this.attributes.cpuType = hardware[1].trim();
            }
            if (model) {
                this.attributes.cpuModel = model[1].trim();
            }
            if (processors) {
                this.attributes.cpuCores = processors.length;
            }
        }

        if (!sample) {
            this.inspectedCPU = false;
            this.attributes.SAAFCPUError = '/proc/stat is not available';
            return;
        }

        this.cpuSample = sample;
        CPU_METRICS.forEach((name) => {
            if (sample[name] != null) {
                this.attributes[name] = sample[name];
            }
        });
        if (sample.contextSwitches != null) {
            this.attributes.contextSwitches = sample.contextSwitches;
        }
        if (sample.vmuptime != null && this.attributes.vmuptime == null) {
            this.attributes.vmuptime = sample.vmuptime;
        }
    }

    /**
     * Compare current /proc/stat counters with the inspectCPU sample.
     * Call this at the end of the request, after inspectCPU.
     */
    inspectCPUDelta() {
        if (!this.inspectedCPU || !this.cpuSample) {
            this.attributes.SAAFCPUDeltaError = 'CPU not inspected before collecting deltas!';
            return;
        }

        const stat = this.readText('/proc/stat');
        const sample = stat ? cpuSample(stat) : null;
        if (!sample) {
            this.attributes.SAAFCPUDeltaError = '/proc/stat is not available';
            return;
        }

        CPU_METRICS.forEach((name) => {
            if (sample[name] != null && this.cpuSample[name] != null) {
                this.attributes[name + 'Delta'] = sample[name] - this.cpuSample[name];
            }
        });
        if (sample.contextSwitches != null && this.cpuSample.contextSwitches != null) {
            this.attributes.contextSwitchesDelta = sample.contextSwitches - this.cpuSample.contextSwitches;
        }
    }

    /**
     * Inspect /proc/meminfo and /proc/vmstat.
     *
     * totalMemory:      Total memory in kB.
     * freeMemory:       Free memory in kB when inspectMemory is called.
     * pageFaults:       Page faults since boot.
     * majorPageFaults:  Major page faults since boot.
     */
    inspectMemory() {
        const memInfo = this.readText('/proc/meminfo');
        if (!memInfo) {
            this.attributes.SAAFMemoryError = '/proc/meminfo is not available';
            return;
        }

        this.inspectedMemory = true;
        memInfo.split('\n').forEach((line) => {
            if (line.startsWith('MemTotal:')) {
                this.attributes.totalMemory = parseInt(line.replace(/MemTotal:\s+/, '').replace(' kB', ''), 10);
            } else if (line.startsWith('MemFree:')) {
                this.attributes.freeMemory = parseInt(line.replace(/MemFree:\s+/, '').replace(' kB', ''), 10);
            }
        });

        const vmStat = this.readText('/proc/vmstat');
        if (!vmStat) {
            this.attributes.SAAFMemoryError = '/proc/vmstat does not exist!';
            return;
        }

        vmStat.split('\n').forEach((line) => {
            const parts = line.trim().split(/\s+/);
            if (parts[0] === 'pgfault') {
                this.attributes.pageFaults = parseInt(parts[1], 10);
            } else if (parts[0] === 'pgmajfault' || parts[0] === 'mgmajfault') {
                this.attributes.majorPageFaults = parseInt(parts[1], 10);
            }
        });
    }

    /**
     * Change in page faults since inspectMemory.
     */
    inspectMemoryDelta() {
        if (!this.inspectedMemory) {
            this.attributes.SAAFMemoryDeltaError = 'Memory not inspected before collecting deltas!';
            return;
        }

        const vmStat = this.readText('/proc/vmstat');
        if (!vmStat) {
            this.attributes.SAAFMemoryDeltaError = '/proc/vmstat does not exist!';
            return;
        }

        vmStat.split('\n').forEach((line) => {
            const parts = line.trim().split(/\s+/);
            if (parts[0] === 'pgfault' && this.attributes.pageFaults != null) {
                this.attributes.pageFaultsDelta = parseInt(parts[1], 10) - this.attributes.pageFaults;
            } else if ((parts[0] === 'pgmajfault' || parts[0] === 'mgmajfault') && this.attributes.majorPageFaults != null) {
                this.attributes.majorPageFaultsDelta = parseInt(parts[1], 10) - this.attributes.majorPageFaults;
            }
        });
    }

    /**
     * Collect information about the current FaaS platform.
     *
     * Lambda Web Functions are recognized by AWS_LAMBDA_HTTP_ENDPOINT together
     * with a Lambda runtime variable such as AWS_LAMBDA_METADATA_API.
     * A local server that only sets AWS_LAMBDA_HTTP_ENDPOINT is reported as Local.
     */
    inspectPlatform() {
        this.inspectedPlatform = true;

        if (this.isLambdaWeb()) {
            const memory = process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE;
            this.attributes.platform = 'AWS Lambda Web';
            this.attributes.functionName = process.env.AWS_LAMBDA_FUNCTION_NAME || null;
            this.attributes.functionMemory = memory != null && memory !== '' ? (Number(memory) || memory) : 2048;
            this.attributes.functionRegion = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || null;
            this.attributes.hostName = os.hostname();
            this.attributes.httpEndpoint = process.env.AWS_LAMBDA_HTTP_ENDPOINT || null;
            if (process.env.AWS_LAMBDA_LOG_STREAM_NAME) {
                this.attributes.containerID = process.env.AWS_LAMBDA_LOG_STREAM_NAME;
            }
            this.readVmId();
            return;
        }

        if (process.env.AWS_LAMBDA_HTTP_ENDPOINT && !process.env.AWS_LAMBDA_LOG_STREAM_NAME) {
            this.attributes.platform = 'Local';
            this.attributes.hostName = os.hostname();
            return;
        }

        if (process.env.AWS_LAMBDA_LOG_STREAM_NAME) {
            this.attributes.platform = 'AWS Lambda';
            this.attributes.containerID = process.env.AWS_LAMBDA_LOG_STREAM_NAME;
            this.attributes.functionName = process.env.AWS_LAMBDA_FUNCTION_NAME;
            this.attributes.functionMemory = process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE;
            this.attributes.functionRegion = process.env.AWS_REGION;
            this.readVmId();
            return;
        }

        if (process.env.X_GOOGLE_FUNCTION_NAME) {
            this.attributes.platform = 'Google Cloud Functions';
            this.attributes.functionName = process.env.X_GOOGLE_FUNCTION_NAME;
            this.attributes.functionMemory = process.env.X_GOOGLE_FUNCTION_MEMORY_MB;
            this.attributes.functionRegion = process.env.X_GOOGLE_FUNCTION_REGION;
            return;
        }

        if (process.env.__OW_ACTION_NAME) {
            this.attributes.platform = 'IBM Cloud Functions';
            this.attributes.functionName = process.env.__OW_ACTION_NAME;
            this.attributes.functionRegion = process.env.__OW_API_HOST;
            const vmID = this.runCommand('cat /sys/hypervisor/uuid').trim();
            if (vmID) {
                this.attributes.vmID = vmID;
            }
            return;
        }

        if (process.env.CONTAINER_NAME) {
            this.attributes.platform = 'Azure Functions';
            this.attributes.containerID = process.env.CONTAINER_NAME;
            this.attributes.functionName = process.env.WEBSITE_SITE_NAME;
            this.attributes.functionRegion = process.env.Location;
            return;
        }

        this.attributes.platform = 'Unknown Platform';
    }

    /**
     * linuxVersion: uname -a output.
     * architecture: uname -m output.
     */
    inspectLinux() {
        this.inspectedLinux = true;
        const version = this.runCommand('uname -a').replace('\n', '').trim();
        const architecture = this.runCommand('uname -m').replace('\n', '').trim();
        if (version) {
            this.attributes.linuxVersion = version;
        }
        if (architecture) {
            this.attributes.architecture = architecture;
        }
    }

    /**
     * Run the initial collectors and record how long they took.
     */
    inspectAll() {
        this.inspectContainer();
        this.inspectPlatform();
        this.inspectLinux();
        this.inspectMemory();
        this.inspectCPU();
        this.addTimeStamp('frameworkRuntime');
    }

    /**
     * Run delta collectors. userRuntime is the time after framework startup
     * and before delta collection, which is the user-function window.
     */
    inspectAllDeltas() {
        if (Object.prototype.hasOwnProperty.call(this.attributes, 'frameworkRuntime')) {
            this.addTimeStamp('userRuntime', this.startTime + this.attributes.frameworkRuntime);
        }

        const deltaTime = Date.now();
        this.inspectCPUDelta();
        this.inspectMemoryDelta();
        this.addTimeStamp('frameworkRuntimeDeltas', deltaTime);
    }

    /**
     * Add a custom attribute to the SAAF object.
     */
    addAttribute(key, value) {
        this.attributes[key] = value;
    }

    /**
     * Read an attribute already stored on this Inspector.
     */
    getAttribute(key) {
        return this.attributes[key];
    }

    /**
     * Store milliseconds from timeSince (or request start) until now.
     */
    addTimeStamp(key, timeSince) {
        if (timeSince == null) {
            timeSince = this.startTime;
        }
        this.attributes[key] = Date.now() - timeSince;
    }

    /**
     * Execute a command and return stdout. Failures return an empty string.
     */
    runCommand(command) {
        try {
            return execSync(command, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
        } catch (err) {
            return '';
        }
    }

    /**
     * Record total runtime and return the collected attributes.
     * Also releases this request from the in-flight count.
     */
    finish() {
        this.addTimeStamp('runtime');
        this.attributes.endTime = Date.now();
        const attributes = this.attributes;
        this.close();
        return attributes;
    }

    /**
     * Drop this request from the in-flight count. Safe to call more than once.
     */
    close() {
        if (!this._open) {
            return;
        }
        this._open = false;
        inFlight = Math.max(0, inFlight - 1);
    }

    readText(path) {
        try {
            return fs.readFileSync(path, { encoding: 'utf8' });
        } catch (err) {
            return null;
        }
    }

    isLambdaWeb() {
        if (!process.env.AWS_LAMBDA_HTTP_ENDPOINT) {
            return false;
        }
        return Boolean(
            process.env.AWS_LAMBDA_METADATA_API ||
            process.env.AWS_LAMBDA_FUNCTION_NAME ||
            process.env.AWS_EXECUTION_ENV ||
            process.env.AWS_LAMBDA_LOG_GROUP_NAME ||
            process.env.AWS_LAMBDA_LOG_STREAM_NAME ||
            process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE
        );
    }

    readVmId() {
        const cgroup = this.readText('/proc/self/cgroup');
        if (!cgroup) {
            return;
        }
        const index = cgroup.indexOf('sandbox-root');
        if (index === -1) {
            return;
        }
        this.attributes.vmID = cgroup.substring(index + 13, index + 19);
    }
}

module.exports = Inspector;
