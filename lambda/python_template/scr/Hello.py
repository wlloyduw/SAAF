# TCSS 499
# Wen Shu
# Winter 2019

# This is just a Hello world python script for
# AWS Lambda function with JSON as input and 
# output

import logging
from Register import *
import time

# my_handler is the lambda function on aws that will be called
# event: is the JSON object or message that passed in
# context: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
# return JSON with customized fields.

def my_handler(event, context):
    myReg = Register()
    try:
        name = event['name']
        message = 'Hello {} from lambda!'.format(name)
        vmSpec = myReg.profileVM()
        vmSpec['message'] = message
        vmSpec['name'] = name
        return vmSpec
    except:
        logger = logging.getLogger()
        logger.setLevel(logging.ERROR)
        logger.error('THE INPUT JSON DOESN\'T HAVE SPECIFIED FIELD.')
        return {
                'error': 'please check log and input JSON'
                }