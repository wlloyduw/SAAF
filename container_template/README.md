If you want to deploy the bash_container template without FaaSET, simply cd into /container_template/functions/bash_container/aws_docker_debian and then run "./build.sh ." to build your docker container and then run "./publish.sh ." to publish the code to AWS. If you want to test run the function call "./run.sh . [json_payload]"

The config.json file contains all of the information defining the deployment. Configure that with your role and profile (this is usually default). 

If you do want to use FaaSET you can use the Deploy_Function.py and Run_Function.py scripts.