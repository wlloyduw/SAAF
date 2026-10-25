# SAAF - Lambda Web Functions

This template deploys a Node.js HTTP server to [AWS Lambda Web Functions](https://docs.aws.amazon.com/lambda/latest/dg/web-functions.html). Lambda runs the server in an execution environment, gives it an HTTPS endpoint, and can reuse that environment for many requests.

The function code follows the JavaScript template: `function.js` is the platform-neutral function, and `Inspector.js` is SAAF. The Web Function bridge in `platforms/aws_web/index.js` only accepts HTTP and forwards a parsed request. Deployment scripts follow the Jupyter template: each platform directory has `build.sh`, `publish.sh`, and `run.sh`.

Lambda Web Functions currently support the `nodejs24.x` runtime. Each execution environment has 2 GB of memory. The server must listen on the host and port in `AWS_LAMBDA_HTTP_ENDPOINT`.

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
            build.sh
            publish.sh
            run.sh
            default_config.json
    deploy
        config.json       Names, region, timeout, and the test payload
        publish.sh
        run.sh
        local.sh
        local.js
```

## Handler

`index.js` listens as soon as it loads. For each request it:

1. Reads the body, up to 1 MB.
2. Parses JSON objects and copies their fields onto the request, so `{"name":"Ada"}` becomes `request.name`. Query parameters fill in fields the body did not set. `method`, `path`, `query`, `headers`, `body`, and `requestId` stay reserved for HTTP data.
3. Calls `function.js` with that request and a context whose `requestId` is the `lambda-web-request-id` header.
4. Returns the object from `Inspector.finish()` as `application/json`.

`GET /`, `GET /?name=Ada`, and `POST /` with a JSON body all hit the same function. Branch on `request.method` and `request.path` when a function needs more than one route.

Lambda sends `SIGTERM` when it removes an environment. The bridge closes the server and exits. Cleanup has about one second.

## SAAF

Create an Inspector at the start of each request, collect metrics, do the work, then collect deltas. Call `finish()` once. `close()` is safe to call again and keeps the in-flight count accurate when a request throws.

```javascript
const Inspector = require('./Inspector');

function yourFunction(request, context) {
    const inspector = new Inspector();
    try {
        inspector.inspectAll();

        inspector.addAttribute('message', 'Hello ' + request.name + '!');

        inspector.inspectAllDeltas();
        return inspector.finish();
    } finally {
        inspector.close();
    }
}
```

`inspectAll()` records the container id, platform, kernel, memory, and CPU counters, then stores `frameworkRuntime`. `inspectAllDeltas()` records `userRuntime` and the counter deltas. `finish()` adds `runtime` and `endTime`.

Web Function environments stay warm and serve later requests in the same process. These fields describe that lifetime:

| Field | Meaning |
| --- | --- |
| uuid | Written to `/tmp/container-id` on the first request in an environment. |
| newcontainer | `1` on that first request, then `0` while the environment lives. |
| invocations | How many Inspectors this process has created. |
| initializationTime | When this process loaded SAAF, in Unix milliseconds. |
| inFlightRequests | Inspectors open at the start of this request, including this one. |
| platform | `AWS Lambda Web` when Lambda runtime variables are present. A local server is `Local`. |
| functionMemory | `AWS_LAMBDA_FUNCTION_MEMORY_SIZE`, or `2048` when Lambda does not set it. |
| functionRegion | `AWS_REGION`. |
| httpMethod, httpPath, requestId | Added by the sample function from the HTTP request. |

CPU and memory counters come from `/proc` and cover the whole environment. With the default `max_concurrency_per_environment` of `1`, a delta belongs to one request. Raising that limit lets one environment handle concurrent requests, and overlapping requests share the same `/proc` counters. `inspectAll()` also reads `/proc` synchronously, which blocks the Node.js event loop for the length of those reads.

The rest of the metric names match the [Node.js Inspector](../nodejs_template/README.md): `cpuUsr`, `cpuKrn`, `vmcpusteal`, `pageFaults`, and their deltas. `majorPageFaults` is read from `pgmajfault`. On a machine without `/proc`, those collectors record `SAAFCPUError` or `SAAFMemoryError` and still return the request timing fields.

## Deploy

Install a current AWS CLI (the release that includes `aws lambda-web`), `jq`, and `curl`. Configure credentials for the target account and Region. From `deploy/`:

```bash
./publish.sh
./run.sh
./run.sh '{"name":"Ada"}'
```

`publish.sh` builds `platforms/aws_web/.build`, uploads it, and creates or updates the Web Function named in `config.json`. The first deploy can create the execution role and the S3 deployment bucket. The endpoint URL is saved to `deploy/endpoint.url`. `run.sh` POSTs the `test` object and prints the JSON body.

Set `DRY_RUN=1` to print the deploy command without calling AWS:

```bash
DRY_RUN=1 ./platforms/aws_web/publish.sh
```

`config.json` fields:

| Field | Role |
| --- | --- |
| function_name | Web Function name. 2–64 letters, numbers, hyphens, or underscores. |
| runtime | `nodejs24.x`. |
| timeout_seconds | Per-request limit from 3 to 900. The Lambda default is 30. |
| max_concurrency_per_environment | Concurrent requests in one environment. This template uses 1 so CPU deltas stay tied to one request. |
| region, profile | AWS CLI target. |
| endpoint_name | Endpoint to create or update. The default name is `dev`. |
| endpoint_type | `HomeRegion`, `MultiRegion`, or `PerRegion`. The type cannot change after creation. |
| auth_type | `ApplicationManaged` lets `run.sh` call the endpoint with curl. `IamAuth` requires signed requests. |
| auto_deployment_mode | `LatestRevision` sends traffic to each new revision when it becomes active. |
| execution_role_arn, bucket_name | Optional existing role and versioned deployment bucket. Empty values let `aws lambda-web deploy` create them. |
| env | Extra environment variables. Lambda rejects reserved names such as `AWS_REGION` and `AWS_LAMBDA_HTTP_ENDPOINT`. |
| test | JSON body used by `run.sh` when no payload is passed. |
| endpoint_url | Optional. When set, `run.sh` uses it instead of looking up the endpoint. |
| function_memory | Documentation for the 2048 MB environment size. Lambda Web Functions do not take a memory setting. |

Edit the function in `src/function.js`, then run `publish.sh` again. The endpoint URL stays the same.

## Run locally

Direct call, with no HTTP server:

```bash
node deploy/local.js
```

HTTP server, using the same bridge Lambda loads:

```bash
./deploy/local.sh
curl -sS -X POST -H 'Content-Type: application/json' -d '{"name":"Ada"}' http://localhost:3000/
```

On macOS, Node binds `localhost` to the IPv6 loopback address. Use `http://localhost:3000/` for that local server.

`./deploy/local.sh` sets `AWS_LAMBDA_HTTP_ENDPOINT` to `localhost:3000` when it is unset. Override that variable to bind a different address.
