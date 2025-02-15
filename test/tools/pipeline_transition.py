#!/usr/bin/env python3

#
# This script allows more complex pipeline state machines to be created by modifying the order in which 
# functions are called. By default functions will just be called linearly but using this allows
# more complex state machines to be created. The order can be changed based on results, functions can
# be skipped altogether or rerun just by changing the index. 
#
# Set the index to -1, None, or a value greater than the number of functions to break out of the loop.
#
# @author Robert Cordingly
#
import ast
import datetime
import json
import os
import random
import requests
import subprocess
import sys
import time
from decimal import Decimal
from threading import Thread

def transition_function(index, functions, experiments, payloads, lastPayload):

    return (index + 1, functions, experiments, payloads, lastPayload)