import base64
import inspect
import subprocess
import os
import shutil
import hashlib
import requests
import json

global sky_mesh

def register_mesh(json_path):
    global sky_mesh
    sky_mesh = json.load(open(json_path))

def get_endpoint(location):
    global sky_mesh
    return sky_mesh[location]

def get_payload_old(main_function, request, dependencies=[], references=[], embeds=[]):
    global sky_mesh

    code = inspect.getsource(main_function)

    function_name = main_function.__name__
    
    for reference in references:
        code += "\n\n" + inspect.getsource(reference)

    if len(dependencies) > 0:
        directory = "./dependencies/" + function_name + "/dynamic_dependencies"
        zip_file = "./dependencies/" + function_name + "/dynamic_dependencies.zip"

        # Check if dependencies folder Exists
        if not os.path.exists("./dependencies"):
            os.mkdir("./dependencies")
        if not os.path.exists("./dependencies/" + function_name):
            os.mkdir("./dependencies/" + function_name)
        if not os.path.exists(directory):
            os.mkdir(directory)

        changed = False
        for dependency in dependencies:
            if not os.path.exists(directory + "/" + dependency):
                subprocess.run(["python3.12", "-m", "pip", "install", dependency, "-t", directory])
                changed = True

        if changed or not os.path.exists(zip_file):
            shutil.make_archive(directory, 'zip', directory)

        file_data = None
        with open(zip_file, 'rb') as f:
            data = f.read()
            file_data = base64.b64encode(data)

        request['d'] = file_data.decode('utf-8')

        hash_object = hashlib.sha256()
        hash_object.update(request['d'].encode())
        request['dh'] = hash_object.hexdigest()

    index = 0
    for func in embeds:
        embed = inspect.getsource(func)
        embed_encoding = base64.b64encode(embed.encode('utf-8')).decode('utf-8')
        code = code.replace("FAASET_EMBED_" + str(index), embed_encoding)
        index += 1
    
    encoding = base64.b64encode(code.encode('utf-8')).decode('utf-8')
    request['f'] = encoding
    return request

import os
import subprocess
import shutil
import base64
import hashlib
import inspect

def get_payload(main_function, request, dependencies=[], references=[], embeds=[]):
    # Extract function source code
    code = inspect.getsource(main_function)
    function_name = main_function.__name__

    for reference in references:
        code += "\n\n" + inspect.getsource(reference)

    if dependencies:
        base_dir = f"./dependencies/{function_name}"
        dependency_dir = f"{base_dir}/dynamic_dependencies"
        zip_file = f"{base_dir}/dynamic_dependencies.zip"

        # Ensure required directories exist
        os.makedirs(dependency_dir, exist_ok=True)

        # Use Docker to install dependencies in Amazon Linux 2
        docker_command = [
            "docker", "run", "--rm",
            "-v", f"{os.path.abspath(dependency_dir)}:/app",
            "amazonlinux:2",
            "bash", "-c",
            "yum install -y python3 pip && pip3 install --upgrade pip && "
            + "pip3 install " + " ".join(dependencies) + " -t /app"
        ]
        subprocess.run(docker_command, check=True)

        # Zip the dependencies
        shutil.make_archive(dependency_dir, 'zip', dependency_dir)

        # Encode the zip file in base64
        with open(zip_file, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode('utf-8')

        # Add to request payload
        request['d'] = file_data
        request['dh'] = hashlib.sha256(file_data.encode()).hexdigest()

    # Embed additional functions
    for idx, func in enumerate(embeds):
        embed_code = inspect.getsource(func)
        embed_encoding = base64.b64encode(embed_code.encode('utf-8')).decode('utf-8')
        code = code.replace(f"FAASET_EMBED_{idx}", embed_encoding)

    # Encode main function code
    request['f'] = base64.b64encode(code.encode('utf-8')).decode('utf-8')

    return request

def run(main_function, request, location, dependencies=[], references=[], embeds=[]):
    request = get_payload(main_function, request, dependencies=dependencies, references=references, embeds=embeds)
    response = requests.post(sky_mesh[location], json=request)
    return response.json()