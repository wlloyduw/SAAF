package saaf;

import java.beans.Introspector;
import java.beans.PropertyDescriptor;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.lang.reflect.InvocationTargetException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 * SAAF
 *
 * @author Wes Lloyd
 * @author Robert Cordingly
 */
public class Inspector {

    /**
     * Global variables that will persist through multiple invocations.
     */
    private static final AtomicInteger invocations = new AtomicInteger(0);
    private static final long initializationTime = System.currentTimeMillis();
    private static final long ticksPerSecond = getTicksPerSecond();

    /**
     * CPU metrics reported by /proc/stat, in the order they appear.
     */
    private static final String[] CPU_METRICS = {"cpuUser", "cpuNice", "cpuKernel", "cpuIdle", "cpuIOWait",
        "cpuIrq", "cpuSoftIrq", "cpuSteal", "cpuGuest", "cpuGuestNice"};

    private final LinkedHashMap<String, Object> attributes;
    private final ArrayList<HashMap<String, Object>> cpuPolls;
    private final long startTime;

    private boolean inspectedCPU = false;
    private boolean inspectedCPUDelta = false;
    private boolean inspectedMemory = false;
    private boolean inspectedMemoryDelta = false;
    private boolean inspectedContainer = false;
    private boolean inspectedPlatform = false;
    private boolean inspectedLinux = false;
    private boolean inspectedEnvironment = false;

    /**
     * Initialize Inspector.
     *
     * attributes: Used to store information collected by each function.
     * version: Inspector version.
     * lang: Function language (java).
     * startTime: The time the function started running.
     * invocations: The number of times an Inspector has been created in this instance.
     * initializationTime: The time SAAF was first loaded by this instance.
     */
    public Inspector() {
        int invocation = invocations.incrementAndGet();

        startTime = System.currentTimeMillis();
        attributes = new LinkedHashMap<>();
        cpuPolls = new ArrayList<>();

        attributes.put("version", 0.8);
        attributes.put("lang", "java");
        attributes.put("startTime", startTime);
        attributes.put("invocations", invocation);
        attributes.put("initializationTime", initializationTime);
    }

    /**
     * Collect information about the runtime container.
     *
     * uuid:         A unique identifier assigned to a container if one does not already exist.
     * newcontainer: Whether a container is new (no assigned uuid) or if it has been used before.
     */
    public void inspectContainer() {
        if (inspectedContainer) {
            attributes.put("SAAFContainerError", "Container already inspected!");
            return;
        }
        inspectedContainer = true;

        //Stamp Container
        int newContainer;
        String uuid = "";

        File f = new File("/tmp/container-id");
        Path p = Paths.get("/tmp/container-id");
        if (f.exists()) {
            newContainer = 0;
            try (BufferedReader br = Files.newBufferedReader(p)) {
                uuid = br.readLine();
                br.close();
            } catch (IOException ioe) {
                //sError = STAMP_ERR_READING_EXISTING_UUID;
            }
        } else {
            newContainer = 1;
            try (BufferedWriter bw = Files.newBufferedWriter(p,
                    StandardCharsets.US_ASCII, StandardOpenOption.CREATE_NEW)) {
                uuid = UUID.randomUUID().toString();
                bw.write(uuid);
                bw.close();
            } catch (IOException ioe) {
                //sError = STAMP_ERR_WRITING_NEW_UUID;
            }
        }

        attributes.put("uuid", uuid);
        attributes.put("newcontainer", newContainer);
    }

    /**
     * Collect information about the CPU assigned to this function.
     *
     * cpuType:      The model name of the CPU.
     * cpuModel:     The model number of the CPU.
     * architecture: The architecture of the CPU (x86 or arm64).
     * cpuCores:     The number of vCPUs allocated to the function.
     * cpuInfo:      A list containing the details of only the first vCPU, without the
     *               flags, bugs, and Features lists.
     *
     * Note: Use inspectCPUInfoVerbose to collect the details of every vCPU.
     */
    public void inspectCPUInfo() {
        inspectCPUInfo(false);
    }

    /**
     * Collect the same information as inspectCPUInfo, except cpuInfo contains
     * every detail of every vCPU, including the flags, bugs, and Features lists.
     */
    public void inspectCPUInfoVerbose() {
        inspectCPUInfo(true);
    }

    /**
     * Parse /proc/cpuinfo and add the CPU info attributes.
     *
     * @param verbose Whether to include the details of every vCPU in cpuInfo.
     */
    private void inspectCPUInfo(boolean verbose) {
        String[] lines = getFileAsString("/proc/cpuinfo").split("\n");

        HashMap<String, Object> coreInfo = new LinkedHashMap<>();
        ArrayList<HashMap<String, Object>> coreList = new ArrayList<>();
        int cpuCount = 0;
        for (String line : lines) {
            String[] keyValue = line.split(":", -1);
            String key = keyValue[0].trim().replace(" ", "_");

            if (key.equals("processor")) {
                cpuCount++;
            } else if (key.equals("power_management") || key.equals("CPU_revision")) {
                coreList.add(coreInfo);
                coreInfo = new LinkedHashMap<>();
                continue;
            }

            if (keyValue.length < 2) {
                continue;
            }
            String value = keyValue[1].trim();

            if (key.equals("flags") || key.equals("bugs") || key.equals("Features")) {
                if (verbose) {
                    coreInfo.put(key, Arrays.asList(value.split(" ", -1)));
                }
            } else {
                coreInfo.put(key, value);
            }
        }

        if (!coreList.isEmpty() && coreList.get(0).containsKey("model_name")) {
            attributes.put("cpuType", coreList.get(0).get("model_name"));
            attributes.put("cpuModel", coreList.get(0).get("model"));
            attributes.put("architecture", "x86");
        } else {
            if (!coreList.isEmpty() && coreList.get(coreList.size() - 1).containsKey("Model")) {
                attributes.put("cpuModel", coreList.get(coreList.size() - 1).get("Model"));
            }
            attributes.put("architecture", "arm64");
        }
        attributes.put("cpuCores", cpuCount);
        attributes.put("cpuInfo", verbose ? coreList : new ArrayList<>(coreList.subList(0, Math.min(1, coreList.size()))));
    }

    /**
     * Collect timing CPU metrics. Each call records a poll of /proc/stat
     * with all CPU times converted from ticks into milliseconds.
     */
    public void pollCPUStats() {
        HashMap<String, Object> data = new LinkedHashMap<>();
        data.put("time", System.currentTimeMillis());

        double tickRate = 1000.0 / ticksPerSecond;

        String[] lines = getFileAsString("/proc/stat").split("\n");
        lines[0] = lines[0].replace("cpu  ", "cpuTotal ");

        for (String line : lines) {
            String[] values = line.split(" ");
            String title = values[0].trim();

            try {
                if (title.contains("cpu")) {
                    HashMap<String, Object> cpuStats = new LinkedHashMap<>();
                    for (int i = 0; i < CPU_METRICS.length; i++) {
                        cpuStats.put(CPU_METRICS[i], Long.parseLong(values[i + 1]) * tickRate);
                    }
                    data.put(title, cpuStats);
                } else if (values.length >= 2) {
                    data.put(title, Long.parseLong(values[1]));
                }
            } catch (NumberFormatException | ArrayIndexOutOfBoundsException e) {
                //Skip lines that are not in the expected format.
            }
        }

        cpuPolls.add(data);
    }

    /**
     * Collect information about the CPU assigned to this function.
     *
     * cpuUser:      Time spent normally executing in user mode.
     * cpuNice:      Time spent executing niced processes in user mode.
     * cpuKernel:    Time spent executing processes in kernel mode.
     * cpuIdle:      Time spent idle.
     * cpuIOWait:    Time spent waiting for I/O to complete.
     * cpuIrq:       Time spent servicing interrupts.
     * cpuSoftIrq:   Time spent servicing software interrupts.
     * cpuSteal:     Time spent waiting for real CPU while hypervisor is using another virtual CPU.
     * cpuGuest:     Time spent running a virtual CPU for guest operating systems.
     * cpuGuestNice: Time spent running a niced guest.
     * bootTime:     Time when the host booted in seconds since the Unix epoch.
     */
    public void inspectCPU() {
        inspectedCPU = true;

        pollCPUStats();

        Map<String, Object> cpuTotal = getCPUTotal(0);
        for (String metric : CPU_METRICS) {
            attributes.put(metric, cpuTotal.get(metric));
        }

        attributes.put("bootTime", cpuPolls.get(0).get("btime"));
    }

    /**
     * Compare information gained from inspectCPU to the current CPU metrics.
     *
     * Note: This function should be called at the end of your function and
     * must be called AFTER inspectCPU.
     *
     * cpuUserDelta:      Time spent normally executing in user mode.
     * cpuNiceDelta:      Time spent executing niced processes in user mode.
     * cpuKernelDelta:    Time spent executing processes in kernel mode.
     * cpuIdleDelta:      Time spent idle.
     * cpuIOWaitDelta:    Time spent waiting for I/O to complete.
     * cpuIrqDelta:       Time spent servicing interrupts.
     * cpuSoftIrqDelta:   Time spent servicing software interrupts.
     * cpuStealDelta:     Time spent waiting for real CPU while hypervisor is using another virtual CPU.
     * cpuGuestDelta:     Time spent running a virtual CPU for guest operating systems.
     * cpuGuestNiceDelta: Time spent running a niced guest.
     */
    public void inspectCPUDelta() {
        if (inspectedCPU) {
            inspectedCPUDelta = true;

            pollCPUStats();

            Map<String, Object> first = getCPUTotal(0);
            Map<String, Object> last = getCPUTotal(cpuPolls.size() - 1);
            for (String metric : CPU_METRICS) {
                attributes.put(metric + "Delta", (Double) last.get(metric) - (Double) first.get(metric));
            }
        } else {
            attributes.put("SAAFCPUDeltaError", "CPU not inspected before collecting deltas!");
        }
    }

    /**
     * Make CPU polls accessible to the function.
     */
    public void processCPUPolls() {
        attributes.put("cpuPolls", cpuPolls);
    }

    /**
     * Inspects /proc/meminfo and /proc/vmstat. Add memory specific attributes:
     *
     * totalMemory:     Total memory allocated to the VM in kB.
     * freeMemory:      Current free memory in kB when inspectMemory is called.
     * pageFaults:      Total number of page faults experienced by the vm since boot.
     * majorPageFaults: Total number of major page faults experienced since boot.
     *
     */
    public void inspectMemory() {

        inspectedMemory = true;
        String memInfo = getFileAsString("/proc/meminfo");
        String[] lines = memInfo.split("\n");
        attributes.put("totalMemory", Long.parseLong(lines[0].replace("MemTotal:", "").replace(" kB", "").trim()));
        attributes.put("freeMemory", Long.parseLong(lines[1].replace("MemFree:", "").replace(" kB", "").trim()));

        String text;

        //Get Memory Metrics
        String filename = "/proc/vmstat";
        File f = new File(filename);
        Path p = Paths.get(filename);
        if (f.exists()) {
            try (BufferedReader br = Files.newBufferedReader(p)) {
                while ((text = br.readLine()) != null && text.length() != 0) {
                    if (text.contains("pgfault")) {
                        String prms[] = text.split(" ");
                        attributes.put("pageFaults", Long.parseLong(prms[1]));
                    } else if (text.contains("pgmajfault")) {
                        String prms[] = text.split(" ");
                        attributes.put("majorPageFaults", Long.parseLong(prms[1]));
                    }
                }

                br.close();
            } catch (IOException ioe) {
                //sb.append("Error reading file=" + filename);
            }
        } else {
            attributes.put("SAAFMemoryError", "/proc/vmstat does not exist!");
        }
    }

    /**
     * Inspects /proc/vmstat to see how specific memory stats have changed.
     *
     * pageFaultsDelta:     The number of page faults experienced since inspectMemory was called.
     * majorPageFaultsDelta: The number of major pafe faults since inspectMemory was called.
     */
    public void inspectMemoryDelta() {
        if (inspectedMemory) {
            inspectedMemoryDelta = true;
            String text;

            //Get CPU Metrics
            String filename = "/proc/vmstat";
            File f = new File(filename);
            Path p = Paths.get(filename);
            if (f.exists()) {
                try (BufferedReader br = Files.newBufferedReader(p)) {
                    while ((text = br.readLine()) != null && text.length() != 0) {
                        if (text.contains("pgfault")) {
                            String prms[] = text.split(" ");
                            attributes.put("pageFaultsDelta", Long.parseLong(prms[1]) - (Long)attributes.get("pageFaults"));
                        } else if (text.contains("pgmajfault")) {
                            String prms[] = text.split(" ");
                            attributes.put("majorPageFaultsDelta", Long.parseLong(prms[1]) - (Long)attributes.get("majorPageFaults"));
                        }
                    }

                    br.close();
                } catch (IOException ioe) {
                    //sb.append("Error reading file=" + filename);
                }
            } else {
                attributes.put("SAAFMemoryDeltaError", "/proc/vmstat does not exist!");
            }
        } else {
            attributes.put("SAAFMemoryDeltaError", "Memory not inspected before collecting deltas!");
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
    public void inspectPlatform() {
        if (inspectedPlatform) {
            attributes.put("SAAFPlatformError", "Platform already inspected!");
            return;
        }
        inspectedPlatform = true;

        String key = System.getenv("AWS_LAMBDA_LOG_STREAM_NAME");
        if (key != null) {
            attributes.put("platform", "AWS Lambda");
            attributes.put("containerID", key);
            attributes.put("functionName", System.getenv("AWS_LAMBDA_FUNCTION_NAME"));
            attributes.put("functionMemory", System.getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"));
            attributes.put("functionRegion", System.getenv("AWS_REGION"));

            StringBuilder cgroup = new StringBuilder();
            for (String line : getFileAsString("/proc/self/cgroup").split("\n")) {
                if (line.contains("2:cpu")) {
                    cgroup.append(line);
                }
            }
            String vmID = cgroup.toString();
            attributes.put("vmID", vmID.substring(Math.min(20, vmID.length()), Math.min(26, vmID.length())));
        } else {
            key = System.getenv("X_GOOGLE_FUNCTION_NAME");
            if (key != null) {
                attributes.put("platform", "Google Cloud Functions");
                attributes.put("functionName", key);
                attributes.put("functionMemory", System.getenv("X_GOOGLE_FUNCTION_MEMORY_MB"));
                attributes.put("functionRegion", System.getenv("X_GOOGLE_FUNCTION_REGION"));
            } else {
                key = System.getenv("__OW_ACTION_NAME");
                if (key != null) {
                    attributes.put("platform", "IBM Cloud Functions");
                    attributes.put("functionName", key);
                    attributes.put("functionRegion", System.getenv("__OW_API_HOST"));
                    attributes.put("vmID", runCommand(new String[]{"cat", "/sys/hypervisor/uuid"}).trim());
                } else {
                    key = System.getenv("CONTAINER_NAME");
                    if (key != null) {
                        attributes.put("platform", "Azure Functions");
                        attributes.put("containerID", key);
                        attributes.put("functionName", System.getenv("WEBSITE_SITE_NAME"));
                        attributes.put("functionRegion", System.getenv("Location"));
                    } else {
                        key = System.getenv("KUBERNETES_SERVICE_PORT_HTTPS");
                        if (key != null) {
                            attributes.put("platform", "OpenFaaS EKS");
                            attributes.put("http_host", System.getenv("Http_Host"));
                            attributes.put("http_foward", System.getenv("Http_X_Forwarded_For"));
                            attributes.put("http_start_time", System.getenv("Http_X_Start_Time"));
                            attributes.put("host_name", System.getenv("HOSTNAME"));
                        } else {
                            attributes.put("platform", "Unknown Platform");
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
     * availableCPUs:     The number of vCPUs available at the current memory setting.
     * utilizedCPUs:      The number of vCPUs utilized while running user code.
     * recommendedMemory: The recommended memory setting for the function.
     */
    private void recommendConfiguration() {
        try {
            if (inspectedPlatform && inspectedCPUDelta) {
                if ("AWS Lambda".equals(attributes.get("platform"))) {
                    Object userRuntime = attributes.get("userRuntime");
                    if (userRuntime == null || ((Number) userRuntime).longValue() == 0) {
                        throw new ArithmeticException("userRuntime must be greater than zero.");
                    }

                    double availableCPUs = Integer.parseInt((String) attributes.get("functionMemory")) / 1792.0;
                    attributes.put("availableCPUs", Math.round(availableCPUs * 1000) / 1000.0);
                    double utilizedCPUs = ((Double) attributes.get("cpuUserDelta")
                            + (Double) attributes.get("cpuKernelDelta")) / ((Number) userRuntime).longValue();
                    attributes.put("utilizedCPUs", Math.round(utilizedCPUs * 1000) / 1000.0);
                    if (availableCPUs - utilizedCPUs < 0.1) {
                        attributes.put("recommendedMemory", Math.min(Math.max(Math.round(0.000556 * (availableCPUs * 1.1) + 0.012346), 128), 10240));
                    } else {
                        attributes.put("recommendedMemory", Math.min(Math.max(Math.round(0.000556 * utilizedCPUs + 0.012346), 128), 10240));
                    }
                }
            } else {
                attributes.put("SAAFRecommendConfigurationError", "CPU, CPU Delta, and Platform must be inspected before recommending a configuration!");
            }
        } catch (Exception e) {
            attributes.put("SAAFRecommendConfigurationError", "Unable to recommend a configuration. " + e.getMessage());
        }
    }

    /**
     * Collect information about the linux kernel.
     *
     * linuxVersion: The version of the linux kernel.
     */
    public void inspectLinux() {
        if (inspectedLinux) {
            attributes.put("SAAFLinuxError", "Linux already inspected!");
            return;
        }
        inspectedLinux = true;
        String linuxVersion = runCommand(new String[]{"uname", "-a"}).trim();
        attributes.put("linuxVersion", linuxVersion);
    }

    /**
     * Collect all environment variables. Each variable is added as an attribute
     * using the variable's name as the key.
     *
     * Note: This is not called by inspectAll. Environment variables may contain
     * secrets, such as the temporary AWS credentials provided by AWS Lambda.
     */
    public void inspectEnvironment() {
        inspectedEnvironment = true;
        attributes.putAll(System.getenv());
    }

    /**
     * Run all data collection methods and record framework runtime.
     */
    public void inspectAll() {
        this.inspectContainer();
        this.inspectCPUInfo();
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
    public void inspectAllDeltas() {

        // Add the 'userRuntime' timestamp.
        if (attributes.containsKey("frameworkRuntime")) {
            this.addTimeStamp("userRuntime", this.startTime + (Long)attributes.get("frameworkRuntime"));
        }

        long deltaTime = System.currentTimeMillis();
        this.inspectCPUDelta();
        this.inspectMemoryDelta();
        this.recommendConfiguration();
        this.addTimeStamp("frameworkRuntimeDeltas", deltaTime);
    }

    /**
     * Add a custom attribute to the output.
     *
     * @param key A string to use as the key value.
     * @param value The value to associate with that key.
     */
    public void addAttribute(String key, Object value) {
        attributes.put(key, value);
    }

    /**
     * Gets a custom attribute from the attribute list.
     *
     * @param key The key of the attribute.
     * @return The object itself. Cast into appropriate data type.
     */
    public Object getAttribute(String key) {
        return attributes.get(key);
    }

    /**
     * Add custom time stamps to the output. The key value determines the name
     * of the attribute and the value will be the time from Inspector
     * initialization to this function call.
     *
     * @param key The name of the time stamp.
     */
    public void addTimeStamp(String key) {
        addTimeStamp(key, startTime);
    }

    /**
     * Add a custom time stamp to the output. This will append the
     * time in milliseconds between the current time and the timeSince variable.
     *
     * @param key The key to add to the output.
     * @param timeSince The time to compare to.
     */
    public void addTimeStamp(String key, long timeSince) {
        Long currentTime = System.currentTimeMillis();
        attributes.put(key, currentTime - timeSince);
    }

    /**
     * Add all attributes of a response object to FaaS Inspector.
     *
     * @param response The response object to consume.
     */
    public void consumeResponse(Response response) {
        Map<String, Object> responseMap = beanProperties(response);
        if (responseMap == null) {
            attributes.put("SAAFConsumeReponseError", "There was an error consuming the response object. See logs for details."+
            "Response object may have fields that were null or could not be cast.");
            return;
        }
        responseMap.keySet().forEach((s) -> {
            attributes.put(s, responseMap.get(s));
        });
    }

    /**
     * Finalize the Inspector. Calculator the total runtime and return the HashMap
     * object containing all attributes collected.
     *
     * @return Attributes collected by the Inspector.
     */
    public HashMap<String, Object> finish() {
        this.addTimeStamp("runtime");
        attributes.put("endTime", System.currentTimeMillis());
        return attributes;
    }

    /**
     * Finalize the Inspector. Calculator the total runtime and return the HashMap
     * object containing all attributes collected and onsume a response object.
     *
     * @return Attributes collected by the Inspector.
     */
    public HashMap<String, Object> finish(Response response) {
        consumeResponse(response);
        return finish();
    }

    /**
     * Get the CPU times of all vCPUs from a CPU poll.
     *
     * @param index The index of the poll.
     * @return The cpuTotal entry of the poll.
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> getCPUTotal(int index) {
        return (Map<String, Object>) cpuPolls.get(index).get("cpuTotal");
    }

    /**
     * Get the number of clock ticks per second used by /proc/stat.
     *
     * @return The value of CLK_TCK, or 100 if it cannot be read.
     */
    private static long getTicksPerSecond() {
        try {
            return Long.parseLong(runCommand(new String[]{"getconf", "CLK_TCK"}).trim());
        } catch (NumberFormatException e) {
            return 100;
        }
    }

    /**
     * Read a file and return it as a String.
     *
     * @param filename The file name/path to read.
     * @return The entire content of the file as a string.
     */
    private static String getFileAsString(String filename) {
        File f = new File(filename);
        Path p = Paths.get(filename);
        String text;
        StringBuilder sb = new StringBuilder();
        if (f.exists()) {
            try (BufferedReader br = Files.newBufferedReader(p)) {
                while ((text = br.readLine()) != null) {
                    sb.append(text);
                    sb.append("\n");
                }
            } catch (IOException ioe) {
                sb.append("Error reading file=");
                sb.append(filename);
            }
        }
        return sb.toString();
    }

    /**
     * Execute a bash command and get the output.
     *
     * @param command An array of strings with each part of the command.
     * @return Standard out of the command.
     */
    private static String runCommand(String[] command) {
        ProcessBuilder processBuilder = new ProcessBuilder();
        processBuilder.command(command);
        try {
            Process process = processBuilder.start();
            StringBuilder output = new StringBuilder();
            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()));

            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line);
                output.append("\n");
            }

            int exitVal = process.waitFor();
            if (exitVal == 0) {
                return output.toString();
            }
        } catch (IOException | InterruptedException e) {
            return "IO Exception " + e.toString();
        }
        return "ERROR";
    }

    /**
     * Convert an Object into a Map using getBeanInfo.
     *
     * @param bean The object to collect methods from.
     * @return A HashMap representation of the object.
     *
     * @author https://bit.ly/2ZGg4uW
     */
    private static Map<String, Object> beanProperties(Object bean) {
        try {
            return Arrays.asList(
                Introspector.getBeanInfo(bean.getClass(), Object.class)
                    .getPropertyDescriptors()
                ).stream()
                // filter out properties with setters only
                .filter(pd -> Objects.nonNull(pd.getReadMethod()))
                .collect(Collectors.toMap(
                        // bean property name
                        PropertyDescriptor::getName,
                        pd -> { // invoke method to get value
                            try {
                                return pd.getReadMethod().invoke(bean);
                            } catch (IllegalAccessException
                            | IllegalArgumentException
                            | InvocationTargetException e) {
                                // replace this with better error handling
                                System.out.println(e.toString());
                                return null;
                            }
                        }));
        } catch (Exception e) {
            // replace this with better error handling
            System.out.println(e.toString());
            return null;
        }
    }
}
