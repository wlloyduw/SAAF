# SAAF - Lambda MicroVMs

This template runs SAAF on [AWS Lambda MicroVMs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-microvms-guide.html) in Python, Node.js, and Java. Lambda builds a MicroVM image by running a Dockerfile, starting the application, and taking a Firecracker snapshot. Each MicroVM started from the image resumes from that snapshot, gets its own HTTPS endpoint, and keeps running until it is suspended or terminated, for up to 8 hours.

Each language folder follows its language template and [web_template](../web_template/). `src` holds the function and the Inspector from [python_template](../python_template/), [nodejs_template](../nodejs_template/), or [java_template](../java_template/). `platforms/aws_microvm` holds the HTTP server, the Dockerfile, and the `build.sh`, `publish.sh`, `run.sh`, and `terminate.sh` scripts, which read a single `config.json`. `publish.sh`, `run.sh`, and `terminate.sh` are the same in all three languages.

MicroVMs run Amazon Linux 2023 on ARM64. Memory is set on the image: 512, 1024, 2048 (the default), 4096, or 8192 MB, with 1 vCPU per 2 GB. A MicroVM can burst to 4 times its baseline memory and vCPUs.

### Layout

```
microvm_template
    python
        src
            handler.py            python_template function
            Inspector.py          SAAF
        platforms/aws_microvm
            server.py             HTTP server Lambda starts
            Dockerfile            Python 3.12 on the Lambda base image
            config.json, build.sh, publish.sh, run.sh, terminate.sh
    nodejs
        src
            function.js           nodejs_template function
            Inspector.js          SAAF
            package.json
        platforms/aws_microvm
            index.js              HTTP server Lambda starts
            Dockerfile            Node.js 24 on the Lambda base image
            config.json, build.sh, publish.sh, run.sh, terminate.sh
    java
        pom.xml
        src/main/java
            microvm/Hello.java    java_template function
            microvm/Server.java   HTTP server Lambda starts
            saaf/Inspector.java   SAAF
            saaf/Response.java
        platforms/aws_microvm
            Dockerfile            Corretto 21 on the Lambda base image
            config.json, build.sh, publish.sh, run.sh, terminate.sh
```

`handler.py`, `function.js`, and `Response.java` are copied unchanged. `Hello.java` is java_template's `lambda.Hello` without the Lambda `RequestHandler` and `Context` types. `pom.xml` is java_template's without `aws-lambda-java-core`, built for Java 21 with Gson 2.11.0, into a shaded jar whose main class is `microvm.Server`.

## Server

Each server listens on port 8080, where Lambda sends the MicroVM's traffic and its lifecycle hooks:

- `POST /aws/lambda-microvms/runtime/v1/ready`: Lambda calls this during the image build, after the server starts. Returning 200 tells Lambda to take the snapshot.
- `POST /aws/lambda-microvms/runtime/v1/run`: Lambda calls this when a MicroVM starts from the snapshot, with the MicroVM's ID. The server writes the ID to `/tmp/microvm-id`. The endpoint forwards traffic only after this hook returns.
- Every other request goes to the function, as in web_template. The server parses the body as JSON and copies its fields onto the request, so `{"name":"Ada"}` becomes `request.name`. Query parameters fill in fields the body did not set. `method`, `path`, `query`, `headers`, and `body` are reserved for the HTTP request. The server returns the object from `Inspector.finish()` as JSON.

`GET /?name=Ada` and `POST /` with a JSON body reach the same function. A body that is not JSON returns 400, and an error thrown by the function returns 500. Requests are handled one at a time, so CPU and memory deltas belong to one request.

## SAAF

Each Inspector is its language template's Inspector with the same kind of changes web_template makes:

1. `inspectPlatform()` only reports MicroVM values. `platform` is always `AWS Lambda MicroVM`, and `containerID` is the MicroVM ID from `/tmp/microvm-id`. `functionName`, `functionMemory`, and `functionRegion` come from `SAAF_FUNCTION_NAME`, `SAAF_FUNCTION_MEMORY`, and `SAAF_FUNCTION_REGION`, which `publish.sh` sets as image environment variables. `vmID` is not reported.
2. `recommendConfiguration` is removed. It assumes Lambda's 1792 MB per vCPU, while MicroVMs have 2048 MB per vCPU and burst to 4 times their baseline, so `availableCPUs`, `utilizedCPUs`, and `recommendedMemory` are not reported.
3. In Node.js, `inspectContainer()` uses `crypto.randomUUID()`, so the package has no dependencies.

Every other method and field matches the language templates, including `inspectCPUInfo()`, `inspectCPUInfoVerbose()`, and `inspectEnvironment()`.

### Snapshots

Lambda starts the server and takes the snapshot before any MicroVM runs, so every MicroVM from an image version starts from the same memory and disk. The servers never call SAAF from a hook, and the functions only load the Inspector on their first request: `handler.py` and `function.js` load it inside the function, and Java loads the `Inspector` class when the first request creates one. So each MicroVM starts its own SAAF values:

- `uuid` and `newcontainer`: `/tmp/container-id` is written on a MicroVM's first request, so each MicroVM has its own `uuid`, and `newcontainer` is `1` only on its first request.
- `invocations` counts requests in the MicroVM, and `initializationTime` is the time of its first request.
- A suspended MicroVM keeps its memory and disk when it resumes, so `invocations` keeps counting and `newcontainer` stays `0`.

Keep this in mind when changing a server or function: anything SAAF records before the `/ready` hook returns is shared by every MicroVM from that image version.

Values the kernel keeps also come from the snapshot. Counters in `/proc`, such as CPU times and page faults, continue from the values captured during the build, so compare deltas rather than totals. `bootTime` is read from the snapshotted kernel and may not tell MicroVMs apart.

## Deploy

Install an AWS CLI v2 recent enough to include `aws lambda-microvms`, plus `jq`, `curl`, and `zip`, and configure credentials for the target account. The Java template also needs Maven, since `build.sh` builds the jar locally. MicroVMs are available in `us-east-1`, `us-east-2`, `us-west-2`, `eu-west-1`, and `ap-northeast-1`.

Before the first publish, set two fields in `config.json`:

1. `bucket`: an S3 bucket in the same Region. `publish.sh` uploads the code artifact to `s3://<bucket>/<function_name>.zip`.
2. `build_role`: the ARN of an IAM role Lambda assumes to build the image.

The build role needs this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "lambda.amazonaws.com" },
    "Action": ["sts:AssumeRole", "sts:TagSession"]
  }]
}
```

And these permissions, with your bucket name:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::<your-bucket-name>/*"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

`execution_role` is optional. It is the role a MicroVM runs with. Without one, Lambda does not send the server's logs to CloudWatch, and the MicroVM cannot call other AWS services. It needs the same trust policy and the `logs` permissions, so the build role also works.

Then, from the language folder:

```bash
./platforms/aws_microvm/publish.sh
./platforms/aws_microvm/run.sh
./platforms/aws_microvm/run.sh '{"name":"Ada"}'
./platforms/aws_microvm/terminate.sh
```

`publish.sh` runs `build.sh`, which copies `src`, the server, and the Dockerfile into `platforms/aws_microvm/.build/app` and zips them into `.build/app.zip`. The Java `build.sh` builds the jar with Maven first and copies only the jar. `publish.sh` uploads the zip to S3, then creates the image on the first publish, or builds a new image version on later ones. It waits while Lambda runs the Dockerfile, starts the server, calls `/ready`, and takes the snapshot. Build logs are in CloudWatch under `/aws/lambda-microvms/<function_name>`. When the image is ready, `publish.sh` terminates MicroVMs still running older image versions.

`run.sh` needs a MicroVM on the latest image version. With `reuse_microvm` set to `true`, it uses a running or suspended one if there is one. Otherwise it starts a new MicroVM and waits for it to run. It then creates a 5-minute auth token for port 8080, POSTs the `test` payload or the JSON argument with the token in the `X-aws-proxy-auth` header, and prints the response. Status messages go to stderr, so stdout is only the response. A suspended MicroVM resumes when the request arrives, so that request includes the time to resume.

Set `reuse_microvm` to `false` to start a new MicroVM for every request, for example to compare MicroVM starts. Each one keeps running until the idle policy suspends it and then terminates it, or until `terminate.sh` runs.

`terminate.sh` terminates every MicroVM started from the image.

Running MicroVMs are billed for their baseline memory and vCPUs whether or not they are serving requests, and for any burst above it. Suspended MicroVMs are billed only for snapshot storage. With the default `idle_policy`, a MicroVM is suspended after 60 seconds without traffic and terminated after 10 minutes suspended, and `maximum_duration` terminates it after 1 hour either way. Run `terminate.sh` when you are done.

`config.json` fields:

| Field | Role |
| --- | --- |
| function_name | MicroVM image name. Letters, numbers, `-`, and `_`, up to 64 characters. |
| region | AWS Region to build and run in. |
| memory | Baseline memory in MB: 512, 1024, 2048, 4096, or 8192. A MicroVM has 1 vCPU per 2048 MB and can burst to 4 times its baseline. |
| bucket | S3 bucket for the code artifact. Required. |
| build_role | IAM role ARN Lambda assumes to build the image. Required. |
| execution_role | Optional IAM role ARN the MicroVM runs with. Needed for the server's logs in CloudWatch. |
| base_image | Lambda MicroVM base image. `aws lambda-microvms list-managed-microvm-images` lists the available images. |
| idle_policy | Passed to `run-microvm`. `maxIdleDurationSeconds` (at least 60) without traffic before the MicroVM is suspended, `suspendedDurationSeconds` suspended before it is terminated, and `autoResumeEnabled` to resume it when a request arrives. |
| maximum_duration | Seconds a MicroVM can exist, running or suspended, from 1 to 28800. |
| reuse_microvm | `true` to send requests to an existing MicroVM on the latest image version, `false` to start a new MicroVM for every request. |
| env | Environment variables to add to the image, as `{"KEY": "value"}`. An image holds up to 50, and `publish.sh` adds 3. |
| test | JSON payload `run.sh` sends when no argument is given. |
