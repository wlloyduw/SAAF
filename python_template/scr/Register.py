# TCSS 499
# Wen Shu
# Winter 2019

# This is just library for profiling the VM's
# spec which your program is running on. It
# targets AWS Lambda for now.

import json
import logging
import os
import subprocess
import re
import uuid
import shlex
import time

# event: is the JSON object or message that passed in.
# return JSON/Dictionary with customized fields.
class Register:
    def __init__(self):
        self.__startTime = time.time()

    def profileVM(self):
        vmbt = self.__getUpTime()
        cpuType = self.__getVmCpuStat()
        myUuid, newContainer = self.__stampContainer()
        cpuMetrics = self.__getCPUMetrics()
        return {
                    'cpuType' : cpuType,
                    'vmuptime' : vmbt,
                    'uuid' : myUuid,
                    'newcontainer' : newContainer,
                    'runtime' : int(round(time.time() - self.__startTime * 1000)),
                    'cpuUsr' : int(cpuMetrics[1]),
                    'cpuNice' : int(cpuMetrics[2]),
                    'cpuKrn' : int(cpuMetrics[3]),
                    'cpuIdle' : int(cpuMetrics[4]),
                    'cpuIowait' : int(cpuMetrics[5]),
                    'cpuIrq' : int(cpuMetrics[6]),
                    'cpuSoftIrq' : int(cpuMetrics[7]),
                    'vmcpusteal' : int(cpuMetrics[8])
                    }
                    
    def __getUpTime(self):
    # https://www.quora.com/Whats-the-difference-between-os-system-and-subprocess-call-in-Python
    # using subprocess.check_output() for linux command
        cliInput = 'grep btime /proc/stat'
        args = shlex.split(cliInput)
        # this returns a bytes object, so I need to decode it into a string.
        f = subprocess.check_output(args).decode('utf-8')
        # temp = f.communicate()
        return int(f.strip().replace('btime ',''))

    def __getVmCpuStat(self):
        # using os.popen() for linux command
        p = os.popen('grep \'model name\' /proc/cpuinfo | head -1')
        result = p.read()
        temp = re.sub('[\n\t]','', result)
        return temp.replace('model name: ', '')
        
    def __getCPUMetrics(self):
        p = os.popen('cat /proc/stat | grep "^cpu" | head -1')
        result = p.read()
        result = result.split()
        return result
    
    def __stampContainer(self):
        myUuid = ''
        newContainer = 1
        if os.path.isfile('/tmp/container-id'):
            stampFile = open('/tmp/container-id', 'r')
            stampID = stampFile.readline()
            myUuid = stampID
            stampFile.close()
            # print('im here! read uuid from file!')
            newContainer = 0
        else:
            stampFile = open('/tmp/container-id', 'w')
            myUuid = str(uuid.uuid4()) # uuid4() generates a random uuid, uuid is not str
            stampFile.write(myUuid)
            stampFile.close()
            # print('im here! write uuid to the file!')
        return myUuid, newContainer