# SAAF Workloads

Node.js workloads for comparing the three ways to run code on AWS Lambda: event functions (the classic FaaS model, [nodejs_template](../nodejs_template/)), [Web Functions](../web_template/), and [MicroVMs](../microvm_template/). Each workload is a folder with the same kernel for all three. `package.sh` stages it into a copy of each paradigm's template for each deployment in `config.json`, so the code, Node.js version, and SAAF measurements are the same and only the platform and its configuration differ.

Most of the workloads are ports of the Python workloads from earlier SAAF experiments: the SeBS benchmarks, calc_service, matrix_calc_service, and the others in `sebs_functions_dynamic.py`. Five are new, chosen to stress different parts of the CPU. Three are I/O workloads for comparing each paradigm's disk and network, and `sleeper` is a control. None have dependencies, and all but `sleeper` can use several threads.

### Layout

```
workloads
    config.json             AWS profile, Region, function name prefix, tags, and the deployments
    package.sh              Stage workloads into .build/<deployment>/<workload>
    publish.sh              Package, deploy, and tag
    tag.sh                  Tag deployed workloads for cost allocation
    run.sh                  Send a request to a deployed workload
    terminate.sh            Terminate a workload's MicroVMs
    local.sh                Run a workload on this machine, without SAAF
    shared
        function.js         SAAF calls around the workload, and the request queue
        runner.js           Parameters, threads, and timings
        worker.js           Worker thread entry point
        random.js           Seeded random numbers
        graph.js            Graph generators for the graph workloads
        files.js            File helpers for the disk workloads
    platforms
        aws_event           Scripts for Lambda event functions
    <workload>
        workload.js         The kernel
        workload.json       Name, description, and default parameters
```

## Workloads

Times are single runs of `workloadRuntime` at the defaults with 1, 2, and 4 threads, on a 2019 MacBook Pro (Intel Core i9-9880H, Node.js 24.22.2) that throttles under load, so treat them as approximate. Expect Lambda to be slower per vCPU. The Python versions ran 4 to 10 seconds each on Lambda at 2048 MB.

| Workload | From | Stresses | Unit | 1 / 2 / 4 threads (s) |
| --- | --- | --- | --- | --- |
| calc_service | SAAF calcs_service | Random array access, arithmetic | One loop | 5.0 / 2.6 / 1.5 |
| matrix_calc_service | matrix_calc_service | Floating-point multiply-add, cache | One pair of products | 5.8 / 3.1 / 1.9 |
| graph_bfs | SeBS graph-bfs | Pointer chasing | One search | 4.1 / 2.3 / 1.2 |
| graph_mst | SeBS graph-mst | Sorting with a comparator, union-find | One spanning tree | 5.3 / 2.7 / 1.5 |
| graph_pagerank | SeBS graph-pagerank | Irregular reads, memory bandwidth | One PageRank | 5.4 / 3.0 / 1.9 |
| sha1_stretcher | sha1_stretcher | Calls into OpenSSL | One hash chain | 5.0 / 2.8 / 1.5 |
| logistic_regression | logistic_regression_parallel | Floating point, `Math.exp` | One shard | 5.1 / 2.6 / 1.6 |
| json_flattener | json_flattener | Strings, objects as dictionaries, GC | One flatten | 5.6 / 3.0 / 2.0 |
| dna_visualization | SeBS dna-visualization | String scanning, sequential writes | One walk | 4.2 / 2.2 / 1.2 |
| thumbnailer | SeBS thumbnailer | Per-pixel integer and floating point | One resize | 4.3 / 2.3 / 1.3 |
| csv_processor | csv_processor | Array allocation, callbacks | One table | 6.0 / 3.0 / 1.6 |
| zipper | zipper | DEFLATE in Node's zlib | One file compressed | 5.8 / 3.1 / 1.9 |
| mandelbrot | New | Floating point in registers | One row | 5.2 / 2.7 / 1.4 |
| nqueens | New | Bitwise integer ops, branches, recursion | One first-two-row placement | 3.1 / 1.6 / 0.9 |
| prime_sieve | New | Strided writes, L2 cache | One segment | 5.7 / 3.0 / 1.6 |
| binary_trees | New | Allocation and garbage collection | One tree | 4.9 / 2.7 / 1.7 |
| log_parser | New | Regular expressions, strings, hash maps | One pass over the log | 6.3 / 3.6 / 2.6 |

The I/O workloads measure the platform's disk, network, and processes more than its CPU, so these local times say little about Lambda. On this laptop, disk_writer goes through the page cache at about 2 GB/s and does not get faster with more threads.

| Workload | From | Measures | Unit | 1 / 2 / 4 threads (s) |
| --- | --- | --- | --- | --- |
| disk_writer | disk_writer | Writing files to /tmp, through the page cache or with `sync` | One file | 2.3 / 2.1 / 2.1 |
| disk_write_and_process | disk_write_and_process | Starting wc, base64, sha1sum, and cat, which read a file and write their output | One run of the 5 commands | 9.0 / 5.0 / 3.3 |
| zipper with `disk: true` | zipper | Reading a file, compressing it, and writing the result | One file compressed | 5.4 / 2.9 / 1.7 |
| http_getter | http_getter | HTTP request latency, with a new connection for each request or one kept alive | One request | Depends on the network |
| sleeper | sleeper | Nothing: a control for overhead and idle cost | The sleep | 1.0 |

Each `workload.js` begins with a comment describing the kernel, and each `workload.json` lists its parameters and defaults. Every workload also takes `threads`, except `sleeper`, and those that generate data take `seed`.

### Parameters

| Workload | Parameters (defaults) |
| --- | --- |
| calc_service | `calcs` 100000 slots per loop, `loops` 2400 |
| matrix_calc_service | `size` 300, `loops` 34 |
| graph_bfs | `size` 100000 nodes, `graph` "tree" or "barabasi", `loops` 3300 |
| graph_mst | `size` 100000, `graph` "tree", `loops` 135 |
| graph_pagerank | `size` 100000, `graph` "tree", `iterations` 100, `loops` 34 |
| sha1_stretcher | `input`, `loops` 1800000 hashes in all, `chains` 16, `algorithm` "sha1" |
| logistic_regression | `samples` 16000, `features` 16, `epochs` 2500, `shards` 16, `learningRate` 0.01 |
| json_flattener | `depth` 10, `breadth` 3, `loops` 10 |
| dna_visualization | `length` 1000000 bases, `loops` 180 |
| thumbnailer | `width` 1920, `height` 1080, `loops` 50, `filter` "bilinear" or "nearest" |
| csv_processor | `size` 100000 rows, `calcs` 14, `loops` 16 |
| zipper | `files` 3, `size` 4 MiB, `loops` 6, `level` 6, `data` "text" or "digits", `disk` false, `dir` "/tmp" |
| mandelbrot | `width` 2000, `height` 2000, `iterations` 1000 |
| nqueens | `n` 15 |
| prime_sieve | `limit` 2000000000, `segmentSize` 262144 odd numbers |
| binary_trees | `depth` 16, `trees` 1500 |
| log_parser | `lines` 100000, `loops` 26 |
| disk_writer | `size` 80 MiB, `loops` 60, `sync` false, `dir` "/tmp" |
| disk_write_and_process | `size` 112 MiB, `loops` 4, `mode` "subprocess" or "node", `dir` "/tmp" |
| http_getter | `url` "https://checkip.amazonaws.com/", `loops` 100, `keepAlive` false, `timeout` 10 seconds |
| sleeper | `time` 1 second |

Runtime grows linearly with `loops` (and `trees`, `height`, `limit`), so those are the parameters to change to make a workload longer or shorter. The graph defaults are sized for the tree graph. The barabasi graph has 10 times as many edges, so it takes several times longer per loop.

### Changes from the Python versions

The ports keep each Python kernel's algorithm, with these changes:

- **Threads split the work.** In calc_service and matrix_calc_service, each Python process did every loop. Here `loops` is the total and threads share it, so a fixed job finishes sooner with more vCPUs. Divide the Python `loops` by the thread count to compare.
- **Defaults are sized for Node.js.** Node.js runs most of these kernels far faster than CPython, roughly 30 to 100 times for the pure-Python ones, so most defaults are larger. The exceptions are json_flattener, where `Object.assign` into large V8 objects is at least 6 times slower than Python's `dict.update`, and sha1_stretcher, where a 20-byte hash takes about 2.5 times as long through Node's OpenSSL 3 as through CPython's `hashlib`. Those two have smaller defaults.
- **The graph workloads use 100,000 nodes, not 5,000,** so each unit does enough work to measure. Graphs use typed arrays in compressed sparse row form. graph_pagerank iterates over edges rather than testing every pair of nodes, and runs a fixed number of iterations. `graph: "barabasi"` matches upstream SeBS, which uses `Graph.Barabasi`. Your ports used `Graph.Tree`, the default.
- **sha1_stretcher splits its loops into `chains`** independent chains so threads can share them. With `chains: 1` it returns the Python version's digest exactly: `{"chains":1,"loops":6000000}` gives `6f7d794f2346de88419707586e3014eb11fcfa10`, as in your sha1_stretcher results.
- **logistic_regression trains one model per shard and averages them.** The Python threads shared one set of weights under the GIL, which has no deterministic equivalent with real threads.
- **zipper compresses in memory by default,** so it measures compression rather than disk. `disk: true` writes the files to /tmp and reads each one back for every unit, as the Python version did. `data: "digits"` repeats `"1234567890"` as the Python version did. The default, `"text"`, is random words, which compress like real logs.
- **disk_write_and_process can do its commands' work in Node.js.** The default, `mode: "subprocess"`, runs wc, base64, sha1sum, and cat as the Python version did. `mode: "node"` does the same reads, work, and writes without starting processes, for comparing the cost of the processes themselves or for a platform without those tools. Both modes report the same `words`, `lines`, `base64Bytes`, `sha1`, and `catBytes`.
- **http_getter takes one `url`.** The Python version looped over `request["url"]` as a list, but your experiments passed a string, so it looped over the URL's characters and every request failed before reaching the network. Threads send requests in parallel. Each request opens a new connection, as Python's `urlopen` did, unless `keepAlive` is set.
- **thumbnailer defaults to bilinear filtering** for more work per pixel. `filter: "nearest"` is the Python algorithm.
- **dna_visualization also computes the squiggle walk** that SeBS's version draws, as well as counting the bases.
- **Buffers that units only overwrite are allocated once per thread.** Allocating a fresh multi-megabyte array per unit made graph_bfs, dna_visualization, and thumbnailer spend their time on page faults, which kept graph_bfs from scaling past 2 threads. csv_processor and binary_trees still allocate per operation, because that is what they measure.

## How a Workload Runs

`function.js` creates the Inspector, calls `inspectAll()`, runs the workload, calls `inspectAllDeltas()`, and returns `finish()`, as the templates' `function.js` does. It loads the Inspector on the first request, so MicroVM snapshots do not capture SAAF state.

The work is divided into units. With `threads: 1`, every unit runs on the main thread. Otherwise `runner.js` starts that many worker threads, and worker *t* runs units *t*, *t* + `threads`, *t* + 2 × `threads`, and so on. Units draw their data from the seed and their own index, so **the results are identical for any thread count and on every platform**. Compare the result attributes across paradigms to confirm they ran the same work. `threads: 0` starts one thread per vCPU the environment reports, and `threads` is never more than the number of units.

Requests run one at a time. A request that arrives while another is running waits in `function.js` before its Inspector starts, so CPU and memory deltas belong to one request, as in the templates.

Fields named in `workload.json`'s defaults are the parameters. Others, such as Web Function headers, are ignored. Query string values are converted to the default's type, so `GET /?loops=10&threads=2` works.

### Attributes

Each response is the SAAF output plus:

| Field | Description |
| --- | --- |
| workload | The workload's name. |
| (parameters) | Every parameter, with the value used. |
| threads | The number of threads used. |
| units | The number of units the work was divided into. |
| (results) | The workload's results, such as `checksum`, `digest`, `solutions`, or `primes`. nqueens, prime_sieve, and binary_trees also report `correct`, checked against known values. |
| setupRuntime | The longest time in ms any thread spent in `setup()`, generating data or writing files. Each thread makes its own copy. |
| computeRuntime | The longest time in ms any thread spent running units. |
| workloadRuntime | The time in ms from starting the threads to having every result. The difference from `computeRuntime` is thread startup. |
| requestId | The Lambda request ID for event functions, and `lambda-web-request-id` for Web Functions. |

## Deploy

Install the AWS CLI with `aws lambda-web` and `aws lambda-microvms` (2.39.1 has both), plus `jq`, `curl`, and `zip`.

`config.json` lists the deployments. Each one names a paradigm and the settings to deploy it with, and every workload is deployed once for each. Web Functions cannot be configured, with 2 vCPUs and 2 GB, so they are the baseline and the others are set as close to them as each paradigm allows:

| Deployment | Paradigm | Configuration |
| --- | --- | --- |
| web | Web Functions | 2 vCPUs and 2048 MB, fixed. ARM64. |
| event-2048 | Event functions | 2048 MB, the same memory. ARM64. Lambda gives 1 vCPU of CPU time per 1769 MB, so this is about 1.16 vCPUs, though it reports 2 cores. |
| event-3072 | Event functions | 3072 MB, for about the same vCPUs. ARM64. This is about 1.74 vCPUs of CPU time. 3538 MB would be exactly 2. |
| microvm | MicroVMs | 2048 MB, with 1 vCPU baseline and bursts up to 4 times that. ARM64. |

Functions are named `<prefix>-<deployment>-<workload>`, with underscores turned into hyphens, such as `saaf-event-2048-graph-bfs`. Deployment names must use only letters, numbers, and hyphens. The other fields:

| Field | Role |
| --- | --- |
| profile | The AWS CLI profile `publish.sh`, `run.sh`, `tag.sh`, and `terminate.sh` use. Leave it out to use `AWS_PROFILE` or the default profile. |
| region | The Region for every deployment. MicroVMs run in `us-east-1`, `us-east-2`, `us-west-2`, `eu-west-1`, and `ap-northeast-1`. |
| tags | Tags for every deployed resource. `tag.sh` adds `deployment`, `paradigm`, and `workload`. |
| role | Required for event deployments, optional for web. The execution role ARN. |
| bucket, build_role | Required for MicroVM deployments. See the [MicroVM README](../microvm_template/README.md#deploy). |
| execution_role | Optional for MicroVM deployments. Needed for the server's logs in CloudWatch. |
| ephemeral_storage | Optional for event deployments. MB of /tmp, from 512, the default, to 10240. |

Any other field in a platform's `config.json` can be set in a deployment too. Those are [aws_event/config.json](./platforms/aws_event/config.json), [aws_web/config.json](../web_template/platforms/aws_web/config.json), and [aws_microvm/config.json](../microvm_template/nodejs/platforms/aws_microvm/config.json). The MicroVM build role's trust policy and logs permissions are also all an event function or Web Function needs, so one role can be used everywhere, as `SAAFMicrovmRole` is here.

```bash
./local.sh mandelbrot '{"threads":2}'      # Check a workload locally, without SAAF
./publish.sh mandelbrot all                # Deploy one workload to every deployment
./publish.sh all event-2048                # Deploy every workload to one deployment
./tag.sh all all                           # Tag everything already deployed
./run.sh mandelbrot web                    # Run it with its defaults
./run.sh mandelbrot microvm '{"threads":0}'
./terminate.sh all                         # Stop every MicroVM
```

`package.sh <workload|all> <deployment|all>` stages a workload in `.build/<deployment>/<workload>`. Each stage has `src` (the template's Inspector and `package.json`, `shared`, and the workload) and the platform folder with a generated `config.json`. Its `test` payload is the workload's defaults. `publish.sh` packages and then runs each stage's own `publish.sh`, and `run.sh` and `terminate.sh` call the stage's scripts. The web and MicroVM scripts are the templates' unchanged, so see their READMEs for what they do. Edit `config.json` here, not in `.build`, which `publish.sh` regenerates.

`tag.sh <workload|all> <deployment|all>` tags each deployed resource with `tags` from `config.json`, plus its `deployment`, `paradigm`, and `workload`, so AWS billing can attribute its costs. It tags the event function, the Web Function, or the MicroVM image. MicroVMs themselves can't be tagged, so `test/workloads` records when each one runs. `publish.sh` runs `tag.sh` after each deploy, and tagging again only replaces the tags' values. Billing uses a tag only after it is activated as a cost allocation tag. See [Measuring Cost](../test/workloads/README.md#measuring-cost).

A MicroVM deployment is an image with a snapshot. `publish.sh` builds the image without starting a MicroVM, `run.sh` starts one from the snapshot when none is running or suspended, and `terminate.sh` stops them. A MicroVM can exist for at most 8 hours, even while suspended, so start them when an experiment begins rather than keeping them for later.

`platforms/aws_event` follows the same pattern for event functions. nodejs_template's `deploy/publish.sh` deploys to four clouds and does not set the architecture or ephemeral storage, so this `publish.sh` sets the runtime, architecture, memory, ephemeral storage, and timeout from `config.json`, and waits for each update to finish. It also gives each function a public function URL with no authentication, so the experiments in `test/workloads` can call all three paradigms over HTTP, and prints the URL. Its `index.js` handler is nodejs_template's, plus reading the request's JSON from a function URL request's body. Its `run.sh` invokes the function with `aws lambda invoke` and prints the response.

## Comparing the Paradigms

All three run Node.js 24: `nodejs24.x` for event and Web Functions, and AL2023's `nodejs24` package in the MicroVM image. Things that still differ:

- **Architecture.** All four deployments run on ARM64. MicroVMs only run on ARM64, and Web Functions report `arm64` in `architecture`, so the event deployments set `architecture` to `arm64`. Add an `x86_64` event deployment to compare with earlier Lambda experiments.
- **CPU.** Event functions get CPU time in proportion to memory, Web Functions have 2 vCPUs and 2 GB, and MicroVMs have 1 vCPU per 2 GB with bursts up to 4 times that. Run each workload at several `threads` values. `cpuCores` is what each environment reports, and `cpuUserDelta`, `cpuStealDelta`, and `utilizedCPUs` (event functions only) show what it got.
- **Warm and cold.** `newcontainer` and `invocations` show whether an environment was new. A MicroVM suspended by its idle policy resumes on the next request, and that request includes the resume time.
- **Billing.** Event functions are billed for each request's duration. Running MicroVMs are billed whether or not they are serving requests. `sleeper` shows what each paradigm charges for time spent waiting.
- **Storage.** Event functions have 512 MB of /tmp unless a deployment's `ephemeral_storage` raises it, up to 10240 MB. At its defaults, disk_write_and_process needs about 270 MB of /tmp for each thread, so more than 1 thread needs more storage. `cpuIOWaitDelta` shows time spent waiting for the disk.
- **Network.** http_getter needs to reach `url`. Event functions outside a VPC can reach the internet, and MicroVMs can through the `INTERNET_EGRESS` network connector the MicroVM `run.sh` attaches. `failedRequests` shows whether a paradigm could reach it, and with the default url, `responseSample` is the public address its requests came from.
- **SAAF.** Each paradigm uses its own template's Inspector. Only event functions report `availableCPUs`, `utilizedCPUs`, and `recommendedMemory`.

## Adding a Workload

Make a folder with a `workload.json`:

```json
{
	"name": "my_workload",
	"description": "One sentence.",
	"defaults": { "loops": 100, "seed": 42, "threads": 1 }
}
```

and a `workload.js` that exports `units(params)`, an optional `setup(params)`, `unit(state, params, index)`, an optional `teardown(state, params)`, and `combine(results, params)`. [runner.js](./shared/runner.js) documents each. Unit results must be structured-cloneable, since worker threads post them back. Use `new Random(derive(params.seed, index))` from `random.js` for per-unit data, and `scratchPath()` from `files.js` for file names that no other thread uses. Then check that `./local.sh my_workload '{"threads":1}'` and `'{"threads":3}'` return the same results. `package.sh all` picks up every folder with a `workload.json`.
