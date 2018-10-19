# faas_inspector

This project provides coding templates to support tracing FaaS function server infrastructure for code deployments.
A generic Hello World function is provided for different FaaS platform/language combinations as a starting point to write infrastructure traceable FaaS functions to enable tracing code containers and hosts (VMs) created by FaaS platform providers for hosting FaaS functions.  This information can help verify the state of infrastructure (COLD vs. WARM) to understand performance results, and help preserve infrastructure for better FaaS performance.

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

| **Platform/Language** | **Description** |
| --------------------- | --------------- |
| lambda/java_template | skeleton hello function for AWS Lambda/Java provided as a mvn project |
