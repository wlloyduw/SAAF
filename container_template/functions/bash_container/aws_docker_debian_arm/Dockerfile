# A better python:buster Dockerfile
# By Robert Cordingly
# Because the one in AWS' docs doesn't work

#FROM python:buster as build-image
FROM arm64v8/python:3.12-slim-bookworm

# Update and install curl. 
# My test script calls RIE using docker exec and having the container 
# make a request to itself using curl. This way I don't have to 
# deal with port forwarding, and having multiple containers 
# running at the same time fighting for ports.
#RUN add-apt-repository -y http://archive.ubuntu.com/ubuntu
RUN apt-get update
RUN apt-get install -y curl jq
#RUN apt-get install -y curl speedtest-cli wget stress software-properties-common

# Download sysbench
#RUN curl -s https://packagecloud.io/install/repositories/akopytov/sysbench/script.deb.sh | bash
#RUN apt -y install sysbench

# Define and create function directory
ENV FUNCTION_DIR="/var/task"
RUN mkdir -p ${FUNCTION_DIR}

# Copy function code
COPY . ${FUNCTION_DIR}

RUN pip install boto3 botocore

# Install the runtime interface client
RUN pip install \
        --target ${FUNCTION_DIR} \
        awslambdaric

# Install the runtime interface emulator
RUN curl -Lo /usr/local/bin/aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie
RUN chmod +x /usr/local/bin/aws-lambda-rie

# Set working directory
WORKDIR ${FUNCTION_DIR}

# Set entry script that determines whether to run RIE if running locally
COPY ./entry_script.sh /entry_script.sh
RUN chmod +x /entry_script.sh
ENTRYPOINT [ "/entry_script.sh" ]

# Set handler
CMD [ "lambda_function.lambda_handler" ]