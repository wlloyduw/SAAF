import Hello
import sys


myName = sys.argv[1]
event = {'name': myName}
context = {}
result = Hello.my_handler(event, context)
print('cmd-line param name=' + myName)
print('function result:')
print(result)