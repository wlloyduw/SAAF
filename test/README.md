# FaaS Runner

FaaS Runner is a tool used to create, execute, and automate experiments on FaaS platforms using SAAF. FaaS Runner works by defining function and experiment JSON files. This project structure allows for experiments to be reused between many different functions.

### Function JSON:

``` json
{
    "function": "helloWorld",
    "platform": "AWS Lambda",
    "source": "../nodejs_template",
    "endpoint": ""
}
```

An example function configuration can be found in [./functions/exampleFunction.json](./functions/exampleFunction.json). Function files provide the core parameters needed to execute and modify a function. Here is a breakdown of the attributes:

* **function:** The name of your function. 
* **platform:** The cloud platform your function is deployed to. This is used to choose the correct CLI to invoke your functions with.
*Accepted options:*
    * AWS Lambda
    * Google
    * IBM
    * Azure
    * HTTP
* **source:** A path to your function's source directory. For some platforms, to change the memory setting your function needs to be rebuilt and redeployed. If using SAAF, FaaS Runner can automatically call the publish.sh script and redeploy your function.
* **endpoint:** If using HTTP or Azure, you must define your function's URL here.

### Experiment JSON:

``` json
{
    "callWithCLI": true,
    "memorySettings": [0],
    "payloads": [
        { "name": "Bob" },
        { "name": "Joe" },
        { "name": "Steve" }
    ],

    "runs": 50,
    "threads": 50,
    "iterations": 3,
    "sleepTime": 5,
    "randomSeed": 42,

    "outputGroups": ["containerID", "cpuType", "vmID", "zAll"],
    "outputRawOfGroup": ["cpuType"],
    "showAsList": ["vmuptime", "cpuType", "vmID"],
    "showAsSum": ["newcontainer"],

    "ignoreFromAll": ["zAll", "lang", "version"],
    "ignoreFromGroups": ["cpuModel", "cpuIdle", "cpuUsr"],
    "ignoreByGroup": {
		"containerID": ["containerID"],
		"cpuType": ["cpuType"],
		"vmID": ["vmID"]
    },
    
    "invalidators": {},
    "removeDuplicateContainers": false,

    "openCSV": true,
    "combineSheets": true,
    "warmupBuffer": 1
} 
```

Experiment files determine how your function with be executed, what setting to use, and how to display the results. Due to this, there are many more ways to customize your experiments. An example experiment configuration can be found in [./experiments/exampleExperiment.json](./experiments/exampleExperiment.json). Here are all of the attributes to define an experiment: 

**Test Settings**
* **callWithCLI:** Boolean - Whether to execute functions with a platforms CLI, or HTTP requests.
* **memorySettings:** Integer List - A list of memory settings to use. If you do not want settings changed, use [0].
* **payload:** Object List - A list of JSON objects to use as payloads. If more than one is listed, these will be randomly distributed across runs.

**Execution Settings**
* **runs:** Integer - The total number of runs to do per iteration.
* **threads:** Integer - The total number of threads to use. If threads is less than runs, multiple runs will be assigned to each thread.
* **iterations:** Integer - The total number of iterations of this experiment to do. 
* **sleepTime:** Integer - The time in seconds to sleep between interations.
* **randomSeed:** Integer - The seed to use randomly distribute payloads.

**Output Settings**

Reports generated by FaaS Runner can have results sorted into groups. These settings define how data is grouped and displayed.

* **outputGroups:** String List - Attributes to group by. For example, entering cpuType will group output by each unique CPU and then calculate averages based on that CPU.
* **outputRawOfGroup:** String List - If an attribute is defined in outputGroup, adding it to this list will automatically list and sort the raw results of every run in a group.
* **showAsList:** String List - Attributes sorting into groups will automatically be discard if they are not a number. Numbers, by default, have an average calculated in the group. Instead of calculating the average for an attribute, or discarding it, add that attribute to this list will instead of a list of attributes.
* **showAsSum:** String List - Similar to showAsList, adding attributes to this list will instead display numeric attributes as a sum rather than an average. This can be useful for counting the total number of an attribute.

**Filter Settings**
* **ignoreFromAll:** String List - These columns of attributes will be completely removed from the entire report.
* **ignoreFromGroups:** String List - These columns will be removed from the sorted groups.
* **ignoreByGroup:** Object List - Individual attributes can be removed from specific groups. For example, if would be redundant to show the cpuType attribute in the cpuType group. This setting allows these example to be  removed. See the example experiment [./experiments/exampleExperiment.json](./experiments/exampleExperiment.json).
* **invalidators:** Object - Runs can be filtered by the value of specific attributes. For example, if a function returns with the "successful" attribute with the value of false. These runs can be filtered by adding a JSON attribute to this object: { "successful": false }.
* **removeDuplicateContainers:** Boolean - This attribute will remove runs that have duplicate containers. This can be useful if you want all of your results to only be runs that ran in parallel.

**Organize Settings**
* **openCSV:** Boolean - After an interation is completed, the CSV report may be automatically opened.
* **combineSheets:** Boolean - If doing an experiment with many iterations, it may be useful to combine all of the sheets together into one "final" report.
* **warmupBuffer:** Integer - If doing a run with multiple iterations, a few iterations can be removed from the combined report. These may be "cold" runs and setting this attribute to 2-3 will guarantee your final report is showing results with warm hardware.

# Running an Experiment:

After defining your function and experiment JSON files, starting an experiment is as simple as run the faas_runner script. 
The script takes a few parameters:

### Example Usage:
``` bash 
# Description of Parameters
./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: OUTPUT PATH}

# Run the example:
./faas_runner.py -f ./functions/exampleFunction.json -e ./experiments/exampleExperiment.json
```
If an output path is not defined, FaaS Runner will save output to the ./history folder.

# Analyzing Results:

Many observations can be made from the default CSV report alone. To support importing data into another tool, such as R, you may want to use the provided [./tools/report_splitter.py](./tools/report_splitter.py) script. This tool will break a FaaS Runner report into a folder of smaller, properly formatted, CSV files.

``` bash 
# Split a report.
./report_splitter.py {PATH TO LARGE CSV}
```





