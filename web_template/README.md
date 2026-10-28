# SAAF - Lambda Web Functions

This template deploys a Node.js HTTP server to [AWS Lambda Web Functions](https://docs.aws.amazon.com/lambda/latest/dg/web-functions.html). Lambda runs the server in an execution environment, gives it an HTTPS endpoint, and reuses that environment for later requests.

`src/function.js` is the function and `src/Inspector.js` is SAAF. `platforms/aws_web` holds the HTTP server Lambda loads and the `build.sh`, `publish.sh`, and `run.sh` scripts, following the Jupyter template's platform folders.

Lambda Web Functions support the `nodejs24.x` runtime. Each execution environment has 2 GB of memory and 2 vCPUs, and there is no memory setting.

### Layout

```
web_template
    src
        function.js       Request logic and SAAF calls
        Inspector.js      SAAF
        package.json
    platforms
        aws_web
            index.js      HTTP server Lambda loads
            config.json   Function name, Region, timeout, and the test payload
            build.sh
            publish.sh
            run.sh
```

## Handler

`index.js` listens on `AWS_LAMBDA_HTTP_ENDPOINT`. For each request it parses the body as JSON and copies its fields onto the request, so `{"name":"Ada"}` becomes `request.name`. Query parameters fill in fields the body did not set. `method`, `path`, `query`, `headers`, `body`, and `requestId` are reserved for the HTTP request. It then calls `function.js` and returns the object from `Inspector.finish()` as JSON.

`GET /?name=Ada` and `POST /` with a JSON body reach the same function. A body that is not JSON returns 400, and an error thrown by the function returns 500. On `SIGTERM`, sent when Lambda removes an environment, the server finishes open requests and exits.

## SAAF

`src/Inspector.js` is the [Node.js Inspector](../nodejs_template/src/Inspector.js) with three changes for Web Functions:

1. `inspectPlatform()` only reports Web Function values: `platform` is always `AWS Lambda Web`, and `functionMemory` and `functionRegion` come from `AWS_LAMBDA_FUNCTION_MEMORY_SIZE` and `AWS_REGION`. Web Functions do not set `AWS_LAMBDA_FUNCTION_NAME` or `AWS_LAMBDA_LOG_STREAM_NAME`, so `functionName` comes from `SAAF_FUNCTION_NAME`, which `publish.sh` sets, and `containerID` and `vmID` are not reported.
2. `inspectContainer()` uses `crypto.randomUUID()`, so the package has no dependencies.
3. `recommendConfiguration` is removed. Web Functions run with a fixed 2048 MB, so there is no memory setting to recommend, and `availableCPUs`, `utilizedCPUs`, and `recommendedMemory` are not reported.

Every other method and field matches the Node.js Inspector, including `cpuInfo`, `cpuUser`, `cpuKernel`, and `cpuSteal` in milliseconds, `bootTime`, `pollCPUStats()`, `processCPUPolls()`, and `inspectEnvironment()`.

```javascript
module.exports = function (request, context) {
    const inspector = new (require('./Inspector'))();
    inspector.inspectAll();

    inspector.addAttribute('message', 'Hello ' + request.name + '!');

    inspector.inspectAllDeltas();
    return inspector.finish();
};
```

Web Function environments stay warm and serve later requests in the same process, so `invocations` counts requests in that process and `newcontainer` is `1` only on an environment's first request. The sample function also adds `httpMethod`, `httpPath`, and `requestId` from the HTTP request.

CPU and memory counters come from `/proc` and cover the whole environment. With `max_concurrency_per_environment` set to `1`, a delta belongs to one request. Raising it lets one environment handle concurrent requests, and overlapping requests share the same `/proc` counters.

## Deploy

Install an AWS CLI that includes `aws lambda-web` (2.38.5 or later works), plus `jq` and `curl`, and configure credentials for the target account. Then:

```bash
./platforms/aws_web/publish.sh
./platforms/aws_web/run.sh
./platforms/aws_web/run.sh '{"name":"Ada"}'
```

`publish.sh` runs `build.sh`, which copies `src` and `index.js` into `platforms/aws_web/.build`, then runs `aws lambda-web deploy`. The first deploy creates the function, its `dev` endpoint, an execution role, and an S3 deployment bucket, and prints the endpoint URL. Later deploys keep the same URL. Each deploy creates a revision, and a function can hold 50, so `publish.sh` deletes revisions that no longer serve traffic.

`run.sh` looks up the `dev` endpoint, POSTs the `test` payload or the JSON argument, and prints the response.

`config.json` fields:

| Field | Role |
| --- | --- |
| function_name | Web Function name. |
| region | AWS Region to deploy to. |
| timeout | Per-request limit in seconds, from 3 to 900. |
| max_concurrency_per_environment | Concurrent requests per environment. Lambda's default is 64. This template uses 1 so CPU and memory deltas belong to one request. |
| role | Optional execution role ARN. When empty, the first deploy creates one. |
| env | Environment variables to add, as `{"KEY": "value"}`. |
| test | JSON payload `run.sh` sends when no argument is given. |
