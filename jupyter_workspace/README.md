# FaaSET - Function-as-a-Service Experiment Toolkit

The FaaSET notebook provides an integrated development environment as a Jupyter notebook to streamline the process of developing Function-as-a-Service (FaaS)
applications, invoke and test functions, execute experiments, train performance models, and process results.
The Function-as-a-Service Experiment Toolkit (FaaSET) notebook
supports many FaaS platforms including AWS Lambda, Google Cloud Functions, IBM Cloud Functions,
Azure Functions, and OpenFaaS. Platform agnostic functions are written inside a Jupyter notebook as standard Python
functions and then are automatically packaged, deployed, and can be invoked from inside the FaaSET notebook. FaaSET builds upon
a strong foundation of tools designed specifically for FaaS development, deployment, and experimentation, such as the Serverless
Application Analytics Framework (SAAF), FaaS Runner, ReportGenerator and more.

### More Articles:

1. [FaaSET Paper](https://dl.acm.org/doi/abs/10.1145/3491204.3527464)
2. [FaaSET Tutorial](../tutorial_faaset/)

# FaaSET Notebook

This Jupyter Notebook provides an interactive platform for FaaS function development, testing, running experiments, and processing results.

# Part 0: Setup Environment

The FaaSET Notebook can be hosted using a variety of different environments. To simplify the setup process, the cells below can be used to automatically configure the environment on Google Colaboratory or Binder.


```python
# Setup Google Colaboratory
!apt update && apt install git jq zip awscli parallel bc curl python3.8 -y
!git clone https://www.github.com/wlloyduw/SAAF 
%pip install requests boto3 botocore tqdm numpy pandas matplotlib ipython jupyter kaleido plotly==5.3.1
%pip install --upgrade awscli

!wget https://bootstrap.pypa.io/get-pip.py
!python3.8 get-pip.py

import os
import sys
os.chdir("./SAAF/jupyter_workspace/src/")
os.mkdir("../../test/history/interactiveExperiment")
os.mkdir("/content/graphs")
```


```python
# Setup Binder Environment
%pip install --upgrade awscli
!wget https://bootstrap.pypa.io/get-pip.py
!python3.8 get-pip.py

import os
import sys
os.mkdir("../../test/history/interactiveExperiment")
os.mkdir("/content/graphs")
```


```python
# Configure AWS Credentials
access_key = "FILL THIS IN"
secret_key = "FILL THIS IN"
region = "us-east-1"
!printf $access_key"\n"$secret_key"\n"$region"\njson\n" | aws configure    
```

## Part 1: Notebook Setup

Welcome to the FaaSET Jupyter notebook! This default notebook provides comments to guide you through all of the main features. If you run into errors or probls please make sure you have the AWS CLI properly configure so that you can deploy function with it, have Docker installed and running, gave execute permission to everything in the /jupyter_workspace and /test directory, and finally installed all the dependencies. You can use quickInstall.sh in the root folder to walk you through the setup process and install dependencies. Other environments may work but getting this notebook to work on cloud based platforms like Google Collab may be very difficult.

Anyway, this first cell is just imports needed to setup the magic that goes on behind the scenes. Run it and it should return nothing. In this cell we define our config object, this object contains any information that we need to deploy functions, such as a role for functions on AWS Lambda. If all of your functions will use the same config object, you can set it globally by using setGlobalConfig. Any methods that take a config object will priorize the object passed to them over the global config.

The setGlobalDeploy function defines that you want your cloud functions to be automatically deployed when they are ran. This can be disabled by setting the method to false.

Function documentation available in jupyter_workspace/platforms/jupyter/interactive_helpers.py



```python
import os
import sys
sys.path.append(os.path.realpath('..'))
from platforms.jupyter.FaaSET import *

```

# Functions

Any function with the @cloud_function decorator will be uploaded to the cloud. Define platforms and memory settings in the decorator. 
Functions are tested locally and must run sucessfully before being deployed.

## Part 2: Deploying Functions

Here is your first cloud function! Creating cloud functions is as simple as writing python functions with (request, context) arguments and adding the @cloud_function decorator! See the two hello world functions below, they are nearly identical! But when we run them we will see that the CPU used on the cloud will be different than our local CPU returned by the SAAF inspector inspectCPUInfo method. That is because the function is running on AWS Lambda! 

You can add arguments to the cloud_function decorator to define the platform you would like to deploy to, the memory setting, and different context objects. Other arguments like references, requirements, and containerize can be used to change behavior.

Cloud functions defined in this notebook do have a few limitations. The main one is that nothing outside the function is deployed to the cloud. That is why imports are inside the function, which is a little weird and can have an effect on what you can import. But for most things this is fine. 

Alongside deploying your function code, you can deploy files alongside this function by adding them to the src/includes_{function name} folder (This function will use src/includes_hello_world). This folder will be automatically created when the function is ran. You can include basically anything, files, scripts, python libraries, whatever you need.

If everything is setup correct, all you need to do is run this code block and you'll get a hello_world function on AWS Lambda! If not all dependencies are installed you can use ./quickInstall.sh to download them.


```python
@FaaSET.cloud_function(platform="AWS")
def hello_world(request, context): 
    from SAAF import Inspector
    inspector = Inspector()
    inspector.inspectCPUInfo()
    inspector.addAttribute("message", "Hello from the cloud " + str(request["name"]) + "!")
    return inspector.finish()

def hello_world_local(request, context): 
    from SAAF import Inspector
    inspector = Inspector()
    inspector.inspectCPUInfo()
    inspector.addAttribute("message", "Hello from your computer " + str(request["name"]) + "!") 
    return inspector.finish()

# Run our local hello_world function and check the CPU.
local = hello_world_local({"name": "Steve"}, None)
print("Local CPU: " + local['cpuType'])

# Run our cloud hello_world function and check the CPU.
cloud = hello_world({"name": "Steve"}, None)
print("Cloud CPU: " + cloud['cpuType'])

```

## Part 3: Chaining Functions and Run Modes

What if we want one cloud function to call another function? This jello_world cloud function is calling the hello_world cloud function we created earlier. What is going to happen? When deployed, could will be generated automatically so that the jello_world function will make a request and call the hello_world function! Simply add any cloud functions that this function calls to the references list and this code will be generated.

This function isn't cheating and just deploying both hello_world and jello_world together, both are deployed as seperate functions and making requests to the other. This example isn't practical but all features of python, such as multithreading, can be used to make multiple requests to functions in parallel. After running, see src/handler_jello_world.py for the automatically generated source code.

Alongside that, this function has a custom run mode. There are three run modes that define how functions are executed when they are called. By default, RunMode.CLOUD is used and calling cloud functions will run them on the cloud. RunMode.LOCAL makes it so that cloud functions are executed locally when called on their own, so to run them on the cloud you must use the test method. As you can see here, we have one single function but like in the previous example we can see different CPUs depending on if it is ran locally or on the cloud using the test method. But, since hello_world is still a cloud function with the default RunMode.CLOUD, it will be called on the cloud instead of running locally. Finally, if you don't want your functions running locally or on the cloud but instead just deployed when the cell is ran you can use RunMode.NONE.


```python
@cloud_function(platform="Local", references=[hello_world])
def jello_world(request, context): 
    from SAAF import Inspector
    inspector = Inspector()
    inspector.inspectAll()
    
    cloud_request = hello_world(request, None)
    hello_message = cloud_request['message']
    jello_message = hello_message.replace("Hello", "Jello")
    inspector.addAttribute("message", jello_message)
    inspector.addAttribute("cloud_request", cloud_request)
    
    inspector.inspectAllDeltas()
    return inspector.finish()


local = jello_world({"name": "Bob"}, None)
print("---")
print("Local jello_world CPU: " + local['cpuType'])
print("Local hello_world call in jello_world CPU: " + local['cloud_request']['cpuType'])

cloud = test(function=jello_world, payload={"name": "Bob"}, quiet=True, skipLocal=True)
print("---")
print("Cloud jello_world CPU: " + cloud['cpuType'])
```

## Part 4: Requirements and Containers

This function here requires the igraph dependency, you can see it defined in the requirements argument of the decorator. For all function builds, you can see the generated files in the /deploy directory. The complete build for this function will be in /deploy/graph_rank_aws_build where you will be able to see all the python files and dependencies. The build folder will be destroyed and recreated every time a function is deployed so it is not recommended to manually edit. 

If the run mode was set to local, any dependencies this function uses would need to be install locally first. But since this function uses the default CLOUD run mode you do not need to install them.

This function also uses more memory than the others, so we have changed the memory setting to 1024MBs instead of the default 256MBs.


```python
%pip install python-igraph

@cloud_function(memory=1024, requirements="python-igraph")
def page_rank(request, context):
    from SAAF import Inspector 
    import datetime
    import igraph
    import time
    
    inspector = Inspector()
    inspector.inspectAll()
    
    size = request.get('size')  
    loops = request.get('loops')

    for x in range(loops):
        graph = igraph.Graph.Tree(size, 10)
        result = graph.pagerank()  

    inspector.inspectAllDeltas()
    return inspector.finish()

page_rank({"size": 10000, "loops": 5}, None)
```

## Containers

To create even more complex execution environments functions can be packaged as Docker containers and deployed to AWS Lambda and IBM Cloud Functions. The function below shows creating the Dockerfile and writing the same function as in the previous example.

First we create the includes_ directory, this is a folder that anything contained in it will be deployed alongside your function. The FaaSET Notebook will look for Dockerfiles in this directory to use instead of the default Docker file. The default just contains the bare minimum to deploy a function as a Docker container. To create more complex environments it is recommended to create your own.


```python
!mkdir ./includes_page_rank_container
```

After creating the includes directory we can write our Dockerfile. In this example we are using the Jupyter writefile magic so we can edit this file directly within the FaaSET Notebook. This Dockerfile includes everything needed to get the Debian python slim buster image running on AWS Lambda. The default Dockerfile will use Amazon Linux 2 rather than a Debian based image. Since we are creating this image from scratch, we need to install some dependencies and the AWS Lambda Runtime Interface Emulator.


```python
%%writefile includes_page_rank_container/Dockerfile
FROM python:3.8-slim-buster
RUN apt-get update
RUN apt-get install -y wget
ENV FUNCTION_DIR="/var/task"
RUN mkdir -p ${FUNCTION_DIR}
COPY . ${FUNCTION_DIR}
RUN pip install igraph
RUN pip install \
        --target ${FUNCTION_DIR} \
        awslambdaric
RUN curl -Lo /usr/local/bin/aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie
RUN chmod +x /usr/local/bin/aws-lambda-rie
WORKDIR ${FUNCTION_DIR}
COPY ./entry_script.sh /entry_script.sh
RUN chmod +x /entry_script.sh
ENTRYPOINT [ "/entry_script.sh" ]
CMD [ "lambda_function.lambda_handler" ]
```

Once our Dockerfile is created we can write the function in the exact same way as we did previously except using the containerize flag in the dectorator rather than defining requirements. Docker containers provide significant advantages as they allow dependencies to be installed in a much simpler way and significantly more configuration options that the default zip packaging method.


```python
@cloud_function(platform="AWS Docker", config={"memory": 1024})
def page_rank_container(request, context):
    from SAAF import Inspector 
    import igraph
    
    inspector = Inspector()
    inspector.inspectAll()
    
    size = request.get('size')  
    loops = request.get('loops')

    for x in range(loops):
        graph = igraph.Graph.Tree(size, 10)
        result = graph.pagerank()  

    inspector.inspectAllDeltas()
    return inspector.finish()

page_rank_container({"size": 10000, "loops": 5}, None)
```

# Execute Experiments

Use FaaS Runner to execute complex FaaS Experiments.

## Part 5: FaaS Runner Experiments

Now, what's cooler than running a function on the cloud once? Running it multiple times! The run_experiment function allows you to create complex FaaS experiments. This function uses our FaaS Runner application to execute functions behind the scenes. It's primary purpose is to run multiple function requests across many threads. You define payloads in the payloads list, choose your memory setting (it will switch settings automatically) and define how many runs you want to do, across how many threads, and how many times you want to repeat the test with iterations. These are the most important parameters, but there are many more defined in the link below. 

After an experiment runs, the results are converted into a pandas dataframe that you can continue using in this notebook. For example you can use matplotlib to generate graphs (see below), or do any other form of data processing. 

Below are two different experiments for our functions. Execute them and generate graphs using the code cells below. You now have experienced all the functionality of the FaaSET Notebook! Happy FaaS developing!



```python
# Define experiment parameters. For more detail see: https://github.com/wlloyduw/SAAF/tree/master/test
hello_experiment = {
  "payloads": [{"name": "Bob"}],
  "memorySettings": [256, 512, 1024],
  "runs": 20,
  "threads": 5,
  "iterations": 1
}

# Execute experiment
hello_world_results = run_experiment(function=hello_world, experiment=hello_experiment)
hello_world_results
```


```python
page_rank_experiment = {
  "payloads": [{"size": 50000, "loops": 5},
                {"size": 100000, "loops": 5},
                {"size": 150000, "loops": 5}],
  "memorySettings": [512],
  "runs": 60,
  "threads": 30,
  "iterations": 1,
  "shufflePayloads": False
}

# Execute experiment
page_rank_results = run_experiment(function=page_rank, experiment=page_rank_experiment)
```


```python
# Functions and Experiments can be written in the same cell!
@cloud_function()
def sleeper(request, context): 
    from SAAF import Inspector
    import time
    inspector = Inspector()
    inspector.inspectAll()
    time.sleep(request['time'])
    inspector.inspectAllDeltas()
    return inspector.finish()

# Test function
print(str(sleeper({"time": 1}, None)))

# Define and execute experiment
sleep_experiment = {
  "payloads": [{"time": 5}],
  "memorySettings": [2048, 4096, 6144],
  "runs": 10,
  "threads": 10,
  "iterations": 1,
}
sleeper_results = run_experiment(function=sleeper, experiment=sleep_experiment)
```

# Process Results

FaaS Runner experiment results are parsed into a Pandas dataframe. This flexibility allows the ability to perform any kind of data processing that you would like.


```python
# Imports for Graphing
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
```


```python
# Define figure style
fig = make_subplots(specs = [[{"secondary_y": False}]])
fig.update_layout(
    barmode='stack',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.47),
    margin=dict(t=0, b=1, l=1, r=1, autoexpand=True),
    font=dict(size=16)
)

workloads = [sleeper_results, sleeper_results, sleeper_results]
names = ["2048 MB", "4096 MB", "6144 MB"]
targetMemory = [2048, 4096, 6144]

finalData = pd.DataFrame()
finalData['workloads'] = names

cpuUsers = [] 
cpuIdles = []
cpuKernels = []
runtimes = []

i = 0
for workload in workloads:
    cpuUsers.append(workload[workload['functionMemory'] == targetMemory[i]]['cpuUserDelta'].mean())
    cpuIdles.append(workload[workload['functionMemory'] == targetMemory[i]]['cpuIdleDelta'].mean())
    cpuKernels.append(workload[workload['functionMemory'] == targetMemory[i]]['cpuKernelDelta'].mean())
    runtimes.append(workload[workload['functionMemory'] == targetMemory[i]]['runtime'].mean())
    i += 1

finalData['cpuUser'] = cpuUsers
finalData['cpuIdle'] = cpuIdles
finalData['cpuKernel'] = cpuKernels
finalData['runtime'] = runtimes

fig.add_trace(go.Bar(x = finalData["workloads"],
                y = finalData["cpuKernel"], 
                name = "CPU Kernel", marker_color="rgba(179, 223, 146, 255)"),
                secondary_y=False)

fig.add_trace(go.Bar(x = finalData["workloads"],
                y = finalData["cpuUser"], 
                name = "CPU User", marker_color="rgba(0, 120, 179, 255)"),
                secondary_y=False)

fig.add_trace(go.Bar(x = finalData["workloads"],
                y = finalData["cpuIdle"], 
                name = "CPU Idle", marker_color="rgba(151, 209, 233, 255)"),
                secondary_y=False)

# Set x-axis title
fig.update_xaxes(title_text="Memory Setting")

# Set y-axes titles
fig.update_yaxes(title_text="CPU Time (ms)", secondary_y=False)

fig.show()
```


```python
# Import matplotlib and setup display.
import matplotlib.pyplot as plt
%matplotlib inline

# Histogram of runtime
plt.hist(page_rank_results['userRuntime'], 10)
```

