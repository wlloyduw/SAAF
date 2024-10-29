import FaaSET
import time

# Apply config, this defines deployment details for your function...
config = {
	"version": "1.0",
	"role": "arn:aws:iam::616835888336:role/service-role/simple_microservice_role",	# REPLACE WITH YOUR ROLE
	"handler": "lambda_function.lambda_handler",
	"subnets": "",
	"security_groups": "",
	"env": "Variables={}",
	"runtime": "python3.12",
	"architectures": "x86_64",
	"timeout": 900,
	"storage": 512,
	"profile": "personal", # REPLACE WITH YOUR PROFILE, this will probably be "default"
	"region": "us-east-1",
	"memory": 512
}

# CHANGING BASH SCRIPT OR DOCKERFILE
# Edit these files in ./functions/bash_container/aws_docker_debian/your_script.sh and ./functions/bash_container/aws_docker_debian/Dockerfile

# Python wrapper function, you probably won't need to change this...
@FaaSET.cloud_function(platform="aws_docker_debian", config=config, force_deploy=True)
def bash_container(request, context): 
    from SAAF import Inspector
    inspector = Inspector() 
    inspector.inspectAll()
    
    import subprocess
    result = subprocess.run(['bash', 'your_script.sh'], capture_output=True, text=True)
    
    output = result.stdout
    error = result.stderr
    
    inspector.addAttribute("standard_output", output)
    inspector.addAttribute("error_output", error)

    inspector.inspectAllDeltas()  
    return inspector.finish()


# Run and deploy...
bash_container({})

# Now run Run_Function.py to invoke the function...