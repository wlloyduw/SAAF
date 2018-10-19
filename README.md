# faas_inspector

This project provides coding templates to support tracing FaaS function server infrastructure for code deployments.
A generic Hello World function is provided for each language as starting point to write infrastructure traceable FaaS functions to support tracing code containers and hosts (VMs). 

__**Example Input/Output:**__

**Input JSON**
```javascript
{
	"Name": "Fred Smith"
}
```

**Output JSON**
```javascript
{
	"value": "Hello Fred Smith",
	"uuid": "cec76fba-9695-4f93-b906-f6eef96543bd",
	"vmuptime": 1539908883,
	"newcontainer": 1
}
```
| **Field** | **Description** |
| --------- | --------------- |
| uuid | the uniquely identifies each container created by AWS |
| vmuptime | provides a unique way to identify the host.  Requires no two hosts to have exactly the same boot time to the nearest second.  In theory it is possible that two VMs could boot at the same time, but it is very rare in the scope of hosting a single Lambda function. |
| newcontainer | 0-indicates the container has been recycled, 1-indicates the container is new |

**Platforms/Languages Supported:**

lambda/java_template - skeleton hello function for AWS Lambda/Java
