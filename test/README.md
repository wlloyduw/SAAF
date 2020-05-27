# FaaS Runner - Run FaaS Experiments

FaaS Runner is a tool used to create, execute, and automate experiments on FaaS platforms using SAAF. FaaS Runner works by defining function and experiment JSON files. This project structure allows for experiments to be reused between many different functions.

### Special Attributes and Attributes Calculated by FaaS Runner

By using FaaS Runner in conjunction with SAAF, many new metrics can be collected that SAAF is unable to find on its own. The table below defines the metrics calculated by FaaS Runner

| **Field** | **Description** |
| --------- | --------------- |
| version | This attribute is used to verify that a run is using SAAF. If this is not included FaaS Runner will not consider it a valid run. |
| 1_run_id | The identifier of a run on a thread.  |
| 2_thread_id | The identifier of a thread of an experiment.  |
| X_avg | By default FaaS Runner will calculate the average of any attributes (X) that can be parsed into a number within categories. |
| X_sum | Using the showAsSum experiment attribute, FaaS Runner will calculate the sum of any attribute (X) that can be parsed into a number within categories. |
| X_list | Using the showAsList experiment attribute, FaaS Runner will create a list of all attributes within categories. |
| roundTripTime | The time between the moment before a request is made and when the response is received in ms. Only calculated with synchronous function invocations. |
| latency | The total runtime attribute subtracted from the roundTripTime in ms. Only calculated with synchronous function invocations. |
| runtimeOverlap | The percent of runtime overlapping with another concurrent run. If two runs both start and end at the exact same moment they would both have 100% runtimeOverlap. Sequential runs have 0%. This calculation can go over 100% with more than 2 concurrent invocations. With n concurrent invocations, a run can have at maximum (n - 1) * 100% runtimeOverlap. This metric can be used to estimate the tenancy of a function and can be filtered using the overlapFilter experiment attribute. Requires both startTime and endTime attributes. |
| payload | FaaS Runner will pass the input payload of a function into the output row. |
| cpuType | The cpuType value returned by SAAF will be concatenated with cpuModel. |
| zTenancy[vmID] | (Deprecated) The tenancy identifier of the function using the vmID attribute as the identifier of function instance hosts. Generally not used anymore as there is no known method of VM identification on AWS Lambda. |
| tenants[vmID] | (Deprecated) The number of tenants a function host may have. |
| zAll | The string "Final Results:" will be appended to all response payloads so that every run can be categorized into one using zAll. |

### Function Attributes and Example Experiment JSON:

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

### Experiment Attributes and Example Experiment JSON:

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

Experiment files determine how your function with be executed, what settings to use, and how to display the results. Due to this, there are many more ways to customize your experiments. An example experiment configuration can be found in [./experiments/exampleExperiment.json](./experiments/exampleExperiment.json). Below are all of the attributes used by an experiment: 

### Test Settings

* **callWithCLI:** Boolean - Whether to execute functions with a platform's CLI, or HTTP requests.
* **callAsync:** Boolean - Current only supported with AWS Lambda, FaaS Runner will make Lambda calls asynchronously.
* **memorySettings:** Integer List - A list of memory settings to use. If you do not want settings changed, use [].
* **parentPayload:** Object - A single JSON object that all further payloads will be based off of. If a JSON payload is large with vary few changing attributes, the parent can be used to reduce the amount of data in the **payloads** attribute.
* **payloads:** Object List - A list of JSON objects to use as payloads. If more than one is listed, these will be distributed across runs. If a parent payload is defined, attributes from parent will be merged into payloads in this list. Attributes defined in this list will take priority over attributes in the parent.
* **payloadFolder:** String - A path to a folder containing JSON files to be used as payloads. Files in that folder will be loaded and used as payloads. Payloads from both **parentPayload** and * **payloads** will be merged. Attributes in **payloads** will take priority over attributes from loaded files.

**Payload Inheritance:** Basic inheritance can be implemented using the parentPayload, payloads list, and payloadFolder. Attributes from each of these payloads will be merged together according to this priority order: 
**payloads > payloadFolder > parentPayload**

## Execution Settings

* **runs:** Integer - The total number of runs to do per iteration.
* **threads:** Integer - The total number of threads to use. If threads is less than runs, multiple runs will be assigned to each thread.
* **iterations:** Integer - The total number of iterations of this experiment to do. 
* **sleepTime:** Integer - The time in seconds to sleep between iterations.
* **randomSeed:** Integer - The seed to use randomly distribute payloads.
* **shufflePayloads:** Boolean - Whether the payloads will be distributed in a random order or sequentially.

## Output Settings

Reports generated by FaaS Runner can have results sorted into groups. These settings define how data is grouped and displayed.

* **outputGroups:** String List - Attributes to group by. For example, entering cpuType will group output by each unique CPU and then calculate averages based on that CPU.
* **outputRawOfGroup:** String List - If an attribute is defined in outputGroup, adding it to this list will automatically list and sort the raw results of every run in a group.
* **showAsList:** String List - Attributes sorting into groups will automatically be discard if they are not a number. Numbers, by default, have an average calculated in the group. Instead of calculating the average for an attribute, or discarding it, add that attribute to this list will instead of a list of attributes.
* **showAsSum:** String List - Similar to showAsList, adding attributes to this list will instead display numeric attributes as a sum rather than an average. This can be useful for counting the total number of an attribute.
* **overlapFilter:** String - When calculating runtime overlap (% of runtime with another function running concurrently) filter only by runs that share this specific attribute.

## Filter Settings

* **ignoreFromAll:** String List - These columns of attributes will be completely removed from the entire report.
* **ignoreFromGroups:** String List - These columns will be removed from the sorted groups.
* **ignoreByGroup:** Object List - Individual attributes can be removed from specific groups. For example, if would be redundant to show the cpuType attribute in the cpuType group. This setting allows these example to be  removed. See the example experiment [./experiments/exampleExperiment.json](./experiments/exampleExperiment.json).
* **invalidators:** Object - Runs can be filtered by the value of specific attributes. For example, if a function returns with the "successful" attribute with the value of false. These runs can be filtered by adding a JSON attribute to this object: { "successful": false }.
* **removeDuplicateContainers:** Boolean - This attribute will remove runs that have duplicate containers. This can be useful if you want all of your results to only be runs that ran in parallel.

## Organize Settings

* **openCSV:** Boolean - After an iteration is completed, the CSV report may be automatically opened.
* **combineSheets:** Boolean - If doing an experiment with many iterations, it may be useful to combine all of the sheets together into one "final" report.
* **warmupBuffer:** Integer - If doing a run with multiple iterations, a few iterations can be removed from the combined report. These may be "cold" runs and setting this attribute to 2-3 will guarantee your final report is showing results with warm hardware.

## Pipeline Settings

For more information about pipeline experiments see the section about Pipeline below.

* **passPayloads:** Boolean - Whether the output of one function should be passed as the input to the next function in the pipeline.
* **transitions:** Object - Attribute key pairs that will allow data to be renamed after a step of a pipeline. For example, if a function returns JSON with an attribute called "output" this can be renamed to "input" by setting transitions to {"output": "input"}.

## Default Attributes

In the event that a function or experiment file is missing attributes, default values will be used instead. These value are defined inside of ./faas_runner.py

# Running an Single-Function Experiment:

After defining your function and experiment JSON files, starting an experiment is as simple as running the faas_runner script. 
The script takes a few parameters:

### Example Usage:
``` bash 
# Description of Parameters
./faas_runner.py -f {PATH TO FUNCTION JSON} -e {PATH TO EXPERIMENT JSON} -o {OPTIONAL: OUTPUT PATH}

# Run the example:
./faas_runner.py -f ./functions/exampleFunction.json -e ./experiments/exampleExperiment.json
```
If an output path is not defined, FaaS Runner will save output to the ./history folder.

## Overwriting Attributes with Command Line Arguments:

Any attribute defined in an function or experiment files can be overwritten using command line arguments. Create a flag starting with -- and then add the attribute name that you would like to overwrite.

For example, overwritten options allows you to easily change the platform of a function without creating an entirely new function file.

``` bash 
# Overwriting the 'platform' attribute of a function..
./faas_runner -f ./function.json -e ./experiment.json --platform IBM
```

By utilizing default options, you can execute an function on AWS Lambda, using the CLI, without even entering a function json file.

``` bash 
# Running a function called 'helloWorld' on AWS Lambda using the default function and experiment attributes.
./faas_runner -e ./experiment.json --function helloWorld
```

Overwritten attributes will attempt to be first casted into numbers, then JSON objects, and finally into strings.

# Analyzing Output Helper Tools:

After running an experiment FaaS Runner will automatically generate a report using the parameters defined in the experiment file. These attributes will filter data, do simple calculations and sort data into categories. Alongside the report, FaaS Runner will also save all of the JSON payloads into a folder alongside the report file. To improve the process of analyizing data, FaaS Runner comes with a few helper programs to help manage data.

## Report Compiler

By default FaaS Runner will save each individual JSON payload to a folder alongside generating the compiled report CSV file. In the event that the final report is generated incorrectly, the report compiler can be used to take a folder of JSON files and generate a new report based off of a experiment file.

### Example Usage:
``` bash 
# Recompile a report.
./compile_results.py {FOLDER PATH} {PATH TO EXPERIMENT JSON}
```

## Report Splitter

Many observations can be made from the default CSV report alone. To support importing data into another tool, such as R, you may want to use the provided [./tools/report_splitter.py](./tools/report_splitter.py) script. This tool will break a FaaS Runner report into a folder of smaller, properly formatted, CSV files.

### Example Usage:
``` bash 
# Split a report.
./report_splitter.py {PATH TO LARGE CSV}
```

# Asynchronous Experiments:

Functions that run asynchronously can still be used with SAAF. Any data returned must be saved onto some storage service and then pulled later after the experiment has finished. The [./s3pull.py](./s3pull.py) script can be used to automate the process of downloading json output files from S3 and reading them. This script will download all files in an S3 bucket, clear the bucket, and compile the downloaded files into a report like regular FaaS Runner experiments. 

### Example Usage:
``` bash 
# Description of Parameters
./s3pull.py {S3 BUCKET NAME} {PATH TO EXPERIMENT JSON} {0/1 CLEAR BUCKET?}

# Pull an experiment:
./s3pull.py saafdump ./experiments/exampleExperiment.json 0
```

# Multi-Function Pipeline Experiments:

FaaS Runner allows multi-function pipeline experiments by using all the same features of single-function experiments. With pipelines, each thread will sequentially execute each function of the pipeline and generate a report when all threads have finished their pipelines.

To create a pipeline, simply supply multiple experiment and function files when calling FaaS Runner. Below shows a three function pipeline made up of 3 function files and 3 experiment files.

``` bash 
# Run a pipeline of 3 functions:
./faas_runner.py -f ./func1.json ./func2.json ./func3.json -e ./exp1.json ./exp2.json ./exp3.json
```

By default, pipelines will use the first experiment file as the "master" experiment. This experiment file will be used to determine how many threads the pipeline uses, the number of runs, and how the output will be generated. The non-master experiment files will be used to determine the respective function's payloads. The function's and experiment's will act as pairs, in the example above func1.json will use exp1.json, func2.json will use exp2.json and so on. The pipeline will execute functions in the order defined here, this behavior can be modified to create much more complicated pipelines.

## Overwriting Attributes in Pipelines with Command Line Arguments:

In the same way that attributes in single-function experiments can be overwritten using command line arguments, attributes in pipelines can be modified in the same way

``` bash 
# Run a pipeline of 3 functions:
./faas_runner.py -f ./func1.json ./func2.json-e ./exp1.json ./exp2.json --platform IBM --callWithCLI[0] 0
```

The example above shows two attributes being overwritten using command line arguments: 'platform' and 'callWithCLI[0]'. The first override ('platform') will apply to ALL functions in the pipeline. The second ('callWithCLI[0]') will only be applied to the FIRST function. You can override specific attributes in specific experiment/function files by adding array-style indices to the end of the attribute name.

Similarly to single-function experiments, overrides allow entire experiments to be created without even needing to use experiment or function JSON files. Pipeline experiments can be defined entirely through command line arguments:

``` bash 
# Run a pipeline of 3 functions:
./faas_runner.py --function[0] hello1 --function[1] hello2 --function[2] hello3 --runs 100 --threads 100 --platform Google
```

The example aboves runs a pipeline experiment of 3 functions named hello1, hello2 and hello3 on Google Cloud Functions. By utilizing the default settings, and command line arguments, complex pipeline experiments can be created through command line arguments alone.

## Customizing the Flow of Pipelines:

By default, pipelines will run each function and experiment sequentially in the order that they are defined in the command line. FaaS Runner includes a Python file called pipeline_transition.py. This file contains one function that is called each time a function in a pipeline is finished. Below is the default transition function.

``` python
#
# Default function transition.
#
# @param index - The last finished function/experiment index.
# @param functions - A list of all function dictionaries for the pipeline.
# @param experiments - A list of all experiment dictionaries for the pipeline.
# @param payloads - A list of payloads assigned to this thread.
# @param lastPayload - The dictionary response from the last function call.
#
# @return The index of the next function/experiment dictionary to use.
#
def transition_function(index, functions, experiments, payloads, lastPayload):
    return index + 1
```

By modifying the index of the next function, complex pipelines that skip or change order of the pipeline can be created based off the results of function responses. The only major limitation to FaaS Runner's pipeline system is that the first function defined in the pipeline will always be the first function called. 
