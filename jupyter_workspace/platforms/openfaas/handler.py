#import sys
#import os

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from . import myFunction
import json

def handle(req):
    return myFunction.yourFunction(json.loads(req), None)
