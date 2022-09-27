# FaaSET Tutorial

Welcome to the Function-as-a-Service Experiment Toolkit tutorial (FaaSET)! FaaSET provides many useful tools to automate and aid in development of FaaS functions deployed to multiple cloud provider.

This tutorial will cover the following topics:

## Outline

0. Setting up FaaSET
1. Creating basic functions with FaaSET
2. Advanced function development
3. Reconfiguring functions
4. Running experiments with FaaSET and FaaS Runner
5. Interactive Activities

## Learning Objectives

1. Learn how to create and deploy functions in a Jupyter Notebook with FaaSET.
2. Run functions locally and on the cloud.
3. Deploy more advanced functions with dependencies, custom Dockerfiles, or other complex deployment options.
4. Reconfigure a previously deployed function on the fly using FaaSET’s reconfigure function.
5. Run an experiment with FaaSET and get common statistics such as average runtime, percentiles, standard deviation, and others.
6. Run an experiment comparing the performance of two functions, run a T-test, or more.

## 0. Setting up FaaSET

At it's core, FaaSET is a Python framework that can be used inside regular Python scripts or Jupyter Notebooks. To create a consistent and streamlined workspace we used Google Colaboratory to host a Notebook to use FaaSET with. The Google Colab notebook can be used to deploy functions to AWS Lambda, Google Cloud Functions, or IBM Cloud Functions. FaaSET is not dependent on Google Colab and can instead be hosted a variety of different ways. This includes using cloud VMs or simply running Jupyter locally. If you would like to host FaaSET locally, you can install the following dependencies:

### FaaSET Generally Dependencies

Run the following bash commands (meant for Ubuntu or other Debian distributions) to install dependencies for FaaSET that are used across all FaaS Platforms.
``` bash
sudo apt update && apt upgrade && apt install git jq zip parallel bc curl python3.8 datamash -y
pip install requests tqdm numpy pandas matplotlib ipython jupyter kaleido plotly==5.3.1
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.8 get-pip.py

git clone -b FaaSET2-beta https://www.github.com/wlloyduw/SAAF 
```

### Utilizing the Demo Platform

If you do not have access to any cloud account, or want to setup to demonstrate some of FaaSET's features, we created the FaaSET Demo platform. This platform will only be available for the duration of the tutorial. The demo platform uses AWS Lambda and runs code by passing it through the request, rather than the full deployment process. This simulates using AWS Lambda as code from FaaSET will be running on Lambda, but some features such as changing the function's configuration are not available.

### AWS Lambda Dependencies

Install dependencies for AWS Lambda:
``` bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Google Cloud Functions Dependencies

``` bash
sudo apt install apt-transport-https ca-certificates gnupg -y
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.gpg
sudo apt update && apt install google-cloud-cli -y
```

### IBM Cloud Functions Dependencies

``` bash
!curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
```

## 1. Creating functions with FaaSET

The key to creating functions with FaaSET is the cloud_function decorator. By adding this decorator to a Python function you can turn it into an application that can be deployed to any of FaaSET's supported platforms! Here is a basic hello_world function, the platform parameter of the cloud function determines which platform this function will be deployed to.

``` python
import FaaSET

@FaaSET.cloud_function(platform = "AWS")
def hello_world(request, context):
    return {"message": "Hello World!"}
```

FaaSET can be utilized both in standard Python scripts and Jupyter Notebooks. For this tutorial we will be utilizing Google Colab to host our Jupyter Notebook, but FaaSET can be ran anywhere. 

### Deploying Functions with FaaSET

After a function is written, all that needs to be done to deploy the function is to call it:

``` python
# Say hello!
hello_world(None, None):
```
``` json
{"message": "Hello World!"}
```

When functions with the cloud_function decorator are called FaaSET goes through a process of first checking if the source code of the function was changed compared to the last time the function was deployed. If the function was changed, the function will be repackaged and deployed on the cloud platform. After these checks and deployment, the function will be called on the cloud and the response from the request will be returned. This automation makes it appear as though you are running functions locally but they are actually running on the cloud! 

To demonstrate that FaaSET is actually running on the cloud, try deploying and running these two functions:

``` python
@FaaSET.cloud_function(platform="AWS")
def cpu_test_cloud(request, context): 
    from SAAF import Inspector
    inspector = Inspector()
    inspector.inspectCPUInfo()
    inspector.addAttribute("message", "Hello from the cloud " + str(request["name"]) + "!")
    return inspector.finish()

def cpu_test_local(request, context): 
    from SAAF import Inspector
    inspector = Inspector()
    inspector.inspectCPUInfo()
    inspector.addAttribute("message", "Hello from your computer " + str(request["name"]) + "!") 
    return inspector.finish()

# Run our cpu_test function without the decorator and check the CPU.
local = cpu_test_local({"name": "Steve"}, None)
print("Local CPU: " + local['cpuType'])

# Run our cpu_test function with the decorator and check the CPU.
cloud = cpu_test_cloud({"name": "Steve"}, None)
print("Cloud CPU: " + cloud['cpuType'])
```

**CHECKPOINT** What does the function return for the cpuType when called with and without the decorator?

### The Serverless Application Analytics Framework

In addition to FaaSET in the previous two functions we also used another tool called SAAF. SAAF is the Serverless Application Analytics Framework, another tool we developed to aid in collecting metrics about serverless functions. SAAF allows profiling of functions on all of FaaSET's supported platforms, profiling takes place inside the function instance allowing deeper observations into the platform than would otherwise be possible by invoking functions alone. 

The metrics from SAAF can also be used in another application we developed, FaaS Runner. FaaS Runner will be used later in the section 4 of this tutorial. In sort, FaaS Runner allows to program complex experiments of function invocations and then makes further observations of FaaS performance such as calculating request latency, concurrency and more. 

### Function Requirements and Limitations

The primary requirement is that the function must take two parameters: a request dictionary, which will contain the values from the request, and a context dictionary which will be platform specific. For maximum platform support, the function name should be all lower case and not contain any special characters. If using platforms such as Google Cloud Functions or Azure make sure your function's name follows the platform's naming requirements. Finally, functions are expected to return a dictionary containing the JSON response of the function.

# 2. Advanced Function Deployment Parameters

In all of the previous examples the only parameter used in *cloud_function* was defining the platform. Alongside platform, the other parameter that can be used is *config*. *Config* is a dictionary that defines all other deployment parameters for functions. These include memory settings, networking configuration, storage, any many more. Each platform has a varying set of configuration options. If configuration attributes are not defined, then the default settings will be used. For example, in the previous functions no memory setting was defined so the default value of 512MBs was used. If we'd like to use a different memory setting we can define the *config* as shown below: 

``` python
import FaaSET

@FaaSET.cloud_function(platform="AWS", 
                       config={"memory": 1024})
def hello_world(request, context):
    return {"message": "Hello World!"}
```

## FaaSET Default Parameters and Folder Structure

Each FaaS platform is different, functions are packaged in different ways, invoked differently, and have different features they support. FaaSET works around this by including unique packaging, deployment, and running scripts for each platform. While functions can be entirely deployed and run using a Jupyter Notebook, FaaSET provides the flexibility to modify the deployment package and processes in any way.

Inside FaaSET there is a platforms and functions folder alongside the Jupyter Notebook or Python script you are using. In the example folder structure below our functions are being written in **workspace.ipynb**. The platforms folder contains all of the build.sh, publish.sh, and run.sh scripts that are used to deploy functions to the platform. In addition, the .default_config.json file contains all of the required parameters for *config* and the default values. Finally, each platform's folder contains any wrappers or other required files to deploy to each platform. If you are using FaaSET for a large number of functions it's recommended to modify the .default_config.json of the platforms it fit you're deployment parameters. 

* /root
  * **workspace.ipynb**
  * /platforms
    * /aws
      * .default_config.json
      * build.sh
      * publish.sh
      * run.sh
    * /google
    * /azure
    * /ibm 
    * and more...
  * /functions
    * /hello_world
      * /.build
      * /experiments
      * source_files...
    * /cpu_test_cloud
      * /.build
      * /experiments
      * source_files...

Each function created in your notebook will create a folder for it in the functions folder. For newly created functions, this will be a copy of the contents of the platform folder, with your function source code added in. Files are only copied from the platform folder to functions when the files do no exist, so if you need to make changes the publishing scripts, or need to modify a requirements.txt file or Dockerfile, they can be modified in a function's folder and will be preserved. **DO NOT** edit files in the .build folder as this directory will be deleted and reconstructed whenever a function is deployed. 

## FaaSET Tips and Debugging

### Force Redeploy

Run into a deployment issue and want to force redeploy a function? FaaSET only deploys functions when they are changed so many an insignificant change (such as adding a space to the end of a line), and run the function again to redeploy it.

### Log Files

Have an error that didn't show up properly in the console? FaaSET keeps logs for all build processes in a function's folder.

### Automatic Function Loading

In large Jupyter Notebooks it can be a hassle to consistently run a whole bunch of cells after starting a new session. FaaSET helps you out by automatically defining previous functions in the workspace when FaaSET is imported. This gives you immediate access to functions and even allows you to create functions in one Notebook and run experiments with them in another without having them defined in both! 

# 3. Reconfigure Functions

If you ever need to change a functions configuration on the fly without change the function’s source code you can use FaaSET’s reconfigure function. Reconfigure can be used to programmatically change a functions configuration as an experiment is run. The reconfigure function executes a function’s publish.sh script without rebuilding the deployment package created in the build.sh script. 

The reconfigure function takes two arguments, the function that you would like to change, and a new *config* dictionary to use. For example in our previous example we deployed the hello_world function with 1 GB of memory. If we changed to change that to 2 GB we could call reconfigure:

``` python
FaaSET.reconfigure(function=hello_world, config={“memory”: 2048})
```

Like with function deployment, if a configuration parameter is not included the platform’s default parameters will be used. 

# 4. Running Experiments with FaaS Runner and FaaSET

FaaS Runner is a tool used to create, execute, and automate experiments on FaaS platforms using SAAF. The primary FaaS Runner application can be used to invoke a large number of functions across many threads, automatically reconfigure functions, run complex pipeliens of multiple functions, and finally compile all of the results into CSV reports with aggregated metrics. 

To work with Jupyter Notebooks and FaaSET, we developed a simplified version of FaaS Runner that is a Python library in addition to the full fledged application. This FaaS Runner Lite version allows defining 'bursts' of function invocations. FaaS Runner Lite does all of the same observations as the main application, such as calculating latency and other client-side metrics. Results from FaaS Runner are then saved in a function's experiments folder. See the example below of running an experiment with our hello_world function:

``` python
import FaaSRunner

FaaSRunner.experiment(function=hello_world,
                      threads=1,
                      runs_per_thread=20,
                      payloads=[{"name": "Bob"},
                                {"name": "Steve"}],
                      experiment_name="hello_experiment")
```

To walk through what this experiment will do, FaaS Runner will call the hello_world function with 1 thread, 20 times sequentially, randomly distribute two payloads to the calls, and finally save the results in ./functions/hello_world/experiments/hello_experiment. A Pandas dataframe will also be returned containing the results of all function invocations. 

If you would like to load the results from a previously ran experiment, or want to run experiments in one Jupyter Notebook and process the results in another, you can use FaaS Runner's load function:

``` python
results = FaaSRunner.load(function=hello_world, experiment="hello_experiment")
```

This function reads the files saved by FaaS Runner and loads them back into a Pandas dataframe for data processing and analysis.

# Interactive Activities

## Activity 1: Deploy a CPU bound function.

In this activity we will deploy a CPU bound function and do some basic experiments that are useful on FaaS platforms. The CPU bound function can be anything as long as CPU performance can impact runtime. For example, an application that does work over a fixed time period would not be applicable. Two functions are available below to use:

Once the application is deployed, run it normally by calling the function in your Jupyter Notebook and collect runtime statistics as shown in the previous examples. 

Next, change the memory setting using the reconfigure function in FaaSET and repeat the same code to collect statistics. How does the performance of the function change? If you increase the memory setting, when does performance stop improving? Does the function run at the lowest possible memory setting (128 MBs).

## Activity 2: Writing Experiments

Deploy 2 CPU bound functions, the Google Colab notebook provides two examples, calc_service and the page_rank function. Then create an experiment with FaaS Runner to run them each 30 time across 30 threads (30 threads, 1 run per thread), name this experiment t_test_demo. Repeat this experiment once with each function. Make sure the results are loaded into the Notebook, either saving the results to a variable when they are run or using FaaSET's load function. Once both experiments are complete print general runtime statistics and run a T-test.








