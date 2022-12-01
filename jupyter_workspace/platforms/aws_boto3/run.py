import boto3
import sys
import json

client = boto3.client('lambda')

response = client.invoke(
    FunctionName=sys.argv[1],
    InvocationType='RequestResponse',
    Payload=json.dumps(sys.argv[2])
)

print(response['Payload'].read().decode("utf-8"))