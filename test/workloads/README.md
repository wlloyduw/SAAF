# Workload Experiments

FaaS Runner experiments for the 18 workloads in `payloads.json`, from [`../../workloads`](../../workloads), on every deployment in its `config.json`: `web`, `event-2048`, `event-3072`, and `microvm`. Every request goes over HTTP:

- **Web Functions:** the function's `dev` endpoint.
- **Event functions:** a public function URL.
- **MicroVMs:** the endpoint of a MicroVM started for the experiment, with an auth token.

| File | Purpose |
| --- | --- |
| `functions/<deployment>/<workload>.json` | FaaS Runner function files, 72 in all. `generate.py` writes them, and git ignores them, since they hold endpoints that need no authentication. |
| `experiments/<workload>/<experiment>.json` | 9 experiment files per workload, all sending the workload's payload from `payloads.json`. |
| `payloads.json` | Each workload's payload, the runtimes it is predicted to have on each deployment, and its measured runtime. |
| `endpoints.json` | The Web Function and event function endpoints. `endpoints.sh` writes it, and git ignores it. |
| `generate.py` | Writes the function and experiment files from `payloads.json`, `endpoints.json`, and `workloads/config.json`. |
| `endpoints.sh` | Reads the endpoints from AWS into `endpoints.json`, then runs `generate.py`. |
| `run.sh` | Runs experiments with FaaS Runner, and records when each one ran. |
| `microvm.sh` | Starts, reauthorizes, and stops the MicroVM that an experiment calls, and records when each one ran. |
| `usage.py` | Collects each MicroVM's lifetime and each event function's billed duration from AWS, to check the bill against. |

## Experiments

| Experiment | Requests |
| --- | --- |
| `sequential-0100` | 100, one at a time |
| `burst-0010`, `burst-0020` | 10 or 20 at once, repeated 10 times |
| `burst-0050`, `burst-0100` | 50 or 100 at once, repeated 5 times |
| `burst-0200` | 200 at once, repeated 3 times |
| `burst-0500` | 500 at once, repeated twice |
| `burst-1000` | 1000 at once, once |
| `pilot` | 3, one at a time, to check a payload's runtime before the others |

FaaS Runner waits 10 seconds between bursts (`sleepTime`). A request with no response after 60 seconds (`timeout`) fails, and the experiment stops after that burst, skipping the rest. Each burst writes its own CSV, and `*-COMBINED.csv` has every burst with an `iteration` column. The 8 experiments other than `pilot` send 3,750 requests per workload and deployment. That is 67,500 requests per deployment across the 18 workloads, and 270,000 across all four deployments.

## Payloads

Each payload uses the workload's defaults with a larger amount of work. CPU-bound workloads set `threads` to 0, which runs one thread per core the platform reports. That is 2 on Web Functions and event functions and 4 on MicroVMs, so the payload measures the CPU each deployment gives. The disk workloads and `http_getter` keep 1 thread.

The amounts of work aim for about 28 seconds on event-2048, the slowest deployment, which keeps every deployment under 30 seconds. The other deployments are 2 to 4 times faster, so Web Functions take about 6 to 16 seconds. mandelbrot, nqueens, and sha1_stretcher have no experiments, to save cost. The table shows predicted runtimes in seconds. The MicroVM column is a range: the low value assumes the MicroVM is bursting on 4 vCPUs, and the high value assumes it is held at its 1 vCPU baseline.

| Workload | Change from defaults | web | event-2048 | event-3072 | microvm |
| --- | --- | ---: | ---: | ---: | ---: |
| binary_trees | `trees` 12,000 | 11 | 29 | 20 | 8–22 |
| calc_service | `loops` 11,000 | 6 | 28 | 19 | 6–19 |
| csv_processor | `loops` 110 | 11 | 27 | 19 | 7–24 |
| disk_write_and_process | `loops` 19 | 16 | 29 | 30 | 23 |
| disk_writer | `loops` 430 | 7 | 28 | 22 | 19 |
| dna_visualization | `loops` 1,900 | 12 | 28 | 19 | 9–28 |
| graph_bfs | `loops` 49,000 | 13 | 28 | 19 | 10–29 |
| graph_mst | `loops` 1,000 | 12 | 28 | 18 | 11–38 |
| graph_pagerank | `loops` 200 | 9 | 29 | 19 | 6–19 |
| http_getter | none | 1 | 1 | 1 | 1 |
| json_flattener | `loops` 72 | 13 | 28 | 19 | 12–29 |
| log_parser | `loops` 140 | 8 | 27 | 18 | 7–18 |
| logistic_regression | `epochs` 28,000 | 15 | 28 | 18 | 9–35 |
| matrix_calc_service | `loops` 230 | 9 | 28 | 19 | 7–21 |
| prime_sieve | `limit` 8,400,000,000 | 11 | 28 | 18 | 8–24 |
| sleeper | `time` 10 | 10 | 10 | 10 | 10 |
| thumbnailer | `loops` 360 | 7 | 28 | 19 | 5–17 |
| zipper | `loops` 44 | 16 | 28 | 19 | 13–35 |

The event-2048 runtimes are measured. Each workload ran once on event-2048 with an earlier payload, in `workloads/results/calibrate-2026-10-29`. Its payload was then scaled linearly to about 28 seconds, and `measured` in `payloads.json` records that run's runtime. The measurements were 0.6 to 1.85 times the earlier predictions: calc_service took 1.85 times as long and graph_pagerank 1.43 times, while graph_bfs and json_flattener took about 0.65 times as long.

event-3072 takes the same correction, since its prediction came from the same event function smoke tests. The Web Function and MicroVM runtimes are still predictions. They scale the single-threaded smoke-test runtimes from `workloads/results/smoke-2026-10-29` by the amount of work, divided by the thread speedup measured on an 8-core laptop. Each smoke test was a single cold request, and 5 of these workloads had no MicroVM result, so treat those columns as estimates. Run `pilot` on each deployment first. If a workload is far off, change its payload in `payloads.json` and run `generate.py`.

- **The CPU varies.** Each deployment runs on a mix of Graviton generations, which SAAF reports in `cpuInfo` as `CPU_part`: `0xd0c` is Graviton2, `0xd40` Graviton3, and `0xd4f` Graviton4. In the smoke tests and the calibration, event functions ran mostly on Graviton2, with some Graviton3 and Graviton4. Web Functions ran mostly on Graviton4, and MicroVMs on Graviton3 and Graviton4. The calibration measured one request per workload, so a workload measured on a faster CPU will take longer on Graviton2. graph_bfs, csv_processor, json_flattener, logistic_regression, binary_trees, and graph_mst were measured on Graviton3 or Graviton4, and on Graviton2 they may take 40 to 55 seconds. calc_service was measured on Graviton2 and will be faster on the others. Each report has a `cpuInfo` category that summarizes each CPU separately.
- **`prime_sieve`** reports `correct` only when `limit` is a power of 10, so with 8.4 billion it reports the count of primes without checking it.
- **`http_getter`** keeps its defaults: 100 requests to `checkip.amazonaws.com`, about 1 second. Reaching 10 seconds would take thousands of requests per call. Across all four deployments, that is billions of requests to a service we don't own. Point `url` at an endpoint you control before increasing `loops`.
- **`disk_write_and_process`** uses 1 thread. Each thread writes its own 112 MB file and up to 151 MB of output, and the event functions have 512 MB of `/tmp`.
- **Memory.** On the laptop, `log_parser` peaked at 760 MB with 2 threads and 1.4 GB with 4. `json_flattener` peaked at 590 MB with 2 threads and 1.1 GB with 4. Everything else stayed under 650 MB.

## Before Running

Do steps 1 to 3 at least a day before the experiments, so that billing can attribute their costs. See [Measuring Cost](#measuring-cost).

1. **Tag what is already deployed.** `../../workloads/tag.sh all all` tags every event function, Web Function, and MicroVM image with `project`, `deployment`, `paradigm`, and `workload`. `publish.sh` also tags whatever it deploys.
2. **Activate the tags for billing.** A tag key appears in Billing and Cost Management up to 24 hours after a resource is first tagged with it. Activate the keys under **Cost allocation tags**, or with:

    ```bash
    aws ce list-cost-allocation-tags --status Inactive --profile personal
    aws ce update-cost-allocation-tags-status --profile personal --cost-allocation-tags-status \
      TagKey=project,Status=Active TagKey=deployment,Status=Active TagKey=paradigm,Status=Active TagKey=workload,Status=Active
    ```

    Activation applies to costs from then on, so activate the keys before the experiments start.
3. **Create a CUR 2.0 data export.** In Billing and Cost Management, open **Data Exports**, create a **Standard data export** of type **CUR 2.0**, and choose **Include resource IDs** and **Hourly** time granularity. Deliver it to an S3 bucket. The console can create the bucket with the policy the export needs.
4. **Republish the event functions.** Function URLs, and the handler that reads a request from one, were added after the smoke tests:

    ```bash
    ../../workloads/publish.sh all event-2048
    ../../workloads/publish.sh all event-3072
    ```

    `platforms/aws_event/publish.sh` creates each function's URL, with no authentication, and the two permissions a public function URL needs. Anyone with a URL can call the function, as with the Web Functions, so keep the URLs private.
5. **Finish the MicroVM images.** 12 of the 18 workloads have tested images: binary_trees, calc_service, csv_processor, disk_write_and_process, disk_writer, dna_visualization, graph_bfs, graph_mst, graph_pagerank, http_getter, json_flattener, and log_parser. The builds for logistic_regression, matrix_calc_service, and prime_sieve were left running and still need a test. sleeper, thumbnailer, and zipper still need publishing.
6. **Fill in the endpoints.** Run `./endpoints.sh`. It reads the Web Function and event function endpoints from AWS, writes `endpoints.json`, and regenerates the function files. `run.sh` skips any deployment whose function file has no endpoint.
7. **Check the account's limits.** `burst-1000` needs 1,000 concurrent executions, which is the default account quota in a Region. Running two event deployments at once needs twice that. Check the quota with `aws service-quotas get-service-quota --service-code lambda --quota-code L-B99A9384`, and the Web Functions' settings with `aws lambda-web get-web-account-settings`. A quota increase can take days, so ask for one early if it is needed.
8. **Run the pilot, and check that the event functions log.** After `./run.sh all all pilot`, `aws logs describe-log-groups --log-group-name-prefix /aws/lambda/saaf-event-` should list a log group for each event function. If one is missing, its execution role cannot write logs, and `usage.py` cannot check that function's bill.

## Running

FaaS Runner needs Python 3 with `requests`, and the AWS CLI. The AWS CLI is needed even for HTTP experiments, because FaaS Runner checks its version on startup.

```bash
./run.sh graph_bfs all pilot              # Check the runtimes first
./run.sh graph_bfs web                    # Every experiment except pilot, in order
./run.sh all event-2048                   # Every workload on one deployment
./run.sh log_parser microvm sequential-0100 burst-0010 burst-0020
```

`run.sh` takes the AWS profile and Region from `workloads/config.json`, and raises the limit on open files to 4096, since each request in a burst has its own connection. It runs one experiment at a time and writes the results to `history/<deployment>/<workload>/`. FaaS Runner's output goes to `<experiment>.log`. After each experiment, it prints the successful requests in each burst, and says so when a timeout stopped the experiment early.

At the predicted runtimes, every experiment for every workload costs roughly:

| Deployment | Estimate |
| --- | ---: |
| event-2048 | $46 |
| event-3072 | $49 |
| web | $44 |
| microvm | about $4 |

The event estimates use the arm64 price of $0.0000133334 per GB-second. The Web Function and MicroVM estimates use third-party figures of $0.0000276944 per vCPU-second and $0.0000036667 per GB-second, so check them against the AWS pricing page. They assume both Web Function vCPUs and all 4 MicroVM vCPUs are busy for each request. They leave out MicroVM image storage, and idle Web Function environments.

Idle Web Function environments are the largest unknown. A Web Function is billed for memory for as long as an environment exists, and AWS doesn't say how long an idle one lasts. `burst-1000` leaves 1,000 environments of 2 GB for each workload, and each minute they stay idle costs about $0.44. Across 18 workloads, that is about $8 per minute of idle time: about $40 if environments last 5 minutes, and about $120 if they last 15.

To find out before spending the budget, run the experiments in stages:

1. Run `pilot` on every deployment.
2. Run every experiment for one workload on every deployment, for example `./run.sh graph_bfs all`.
3. Wait a day, then look up that workload's costs in the CUR data. For the Web Function, compare the memory GB-seconds with its active vCPU-seconds to see how long environments stayed idle.
4. Run the other workloads, or drop `burst-0500` and `burst-1000` from the Web Functions if idle environments cost too much.

An AWS Budgets alert, at $100 and $200 for example, warns by email when costs pass a threshold. Billing data arrives hours late, so an alert doesn't stop spending in time.

### MicroVMs

For each experiment on a MicroVM deployment, `run.sh` does the following:

1. `microvm.sh start` runs a MicroVM from the image's latest version and waits for its `/run` hook.
2. `microvm.sh start` writes `.microvm/<deployment>/<workload>/function.json` with the MicroVM's endpoint, and `headers.json` with a 60-minute auth token. FaaS Runner reads the token from `headersFile` on every request.
3. `run.sh` runs the experiment and gets a new token every 45 minutes.
4. `run.sh` terminates the MicroVM. It also does this if the script is interrupted with Ctrl-C or `kill`.

`microvm.sh stop <workload> microvm suspend` suspends a MicroVM instead of terminating it. `../../workloads/terminate.sh all` terminates every MicroVM left running. A MicroVM ends after `MAXIMUM_DURATION` seconds regardless, 28,800 (8 hours) by default and at most. It suspends after 15 idle minutes.

A MicroVM runs one request at a time, so the requests in a burst wait in line. With the 60-second timeout, a burst that a MicroVM can't finish in a minute fails its remaining requests, and the experiment stops there. At 10 seconds per request, about 6 requests in each MicroVM burst succeed, and every burst experiment then stops after its first burst. `sequential-0100` never waits in line, so it runs in full. That keeps each MicroVM experiment to a few minutes, about 10 MicroVM-hours in all.

## Measuring Cost

The bill is the authority: AWS's CUR 2.0 data, with each resource's ID and tags. The other records place each experiment in time, and give a second count of the usage to check the bill against.

| Record | Event functions | Web Functions | MicroVMs |
| --- | --- | --- | --- |
| CUR 2.0 data | Tagged, by function | Tagged, by Web Function | Images are tagged. MicroVMs cannot be tagged, so match their resource IDs. |
| `history/experiments.csv` from `run.sh` | Each experiment's UTC start and finish, and its successful, failed, and timed-out requests | Same | Same, with the experiment's MicroVM |
| `history/microvms.jsonl` from `microvm.sh` | | | Lambda's description of each MicroVM when it started, ran, and terminated, labeled with its experiment |
| `history/microvm-lifetimes.csv` from `usage.py` | | | Every MicroVM of every image: Lambda's `startedAt`, `terminatedAt`, and seconds running |
| `history/event-usage.csv` from `usage.py` | Invocations and billed duration, from the `REPORT` line Lambda logs for each invocation | | |

After the experiments:

1. **Make sure nothing is still running.** Run `../../workloads/terminate.sh all`, then `python3 usage.py`. `usage.py` warns about any MicroVM that has not terminated, since one is billed until it does. Run `usage.py` soon after the experiments, since how long Lambda lists terminated MicroVMs isn't documented. It only reads from AWS, and its window runs from the first experiment in `experiments.csv` to an hour after the last.
2. **Wait for the bill to settle.** CUR data arrives up to 3 times a day, so wait at least 24 hours after the last experiment. Web Functions are billed for memory for as long as an environment exists, including idle time after an experiment, and the tags cover that time too.
3. **Query the CUR data,** with Athena, or with DuckDB on the downloaded Parquet files. User-defined tags appear in `resource_tags` with a `user_` prefix:

    ```sql
    SELECT resource_tags['user_deployment'] AS deployment, line_item_usage_type,
           SUM(line_item_usage_amount) AS usage, pricing_unit,
           SUM(pricing_public_on_demand_cost) AS list_price, SUM(line_item_unblended_cost) AS charged
    FROM cur
    WHERE resource_tags['user_project'] = 'saaf-workloads'
      AND line_item_line_item_type IN ('Usage', 'DiscountedUsage', 'SavingsPlanCoveredUsage')
    GROUP BY 1, 2, 4
    ORDER BY 1, 2
    ```

    Report the usage and its list price, not the amount charged. The account's credits, Lambda's monthly free tier (1 million requests and 400,000 GB-seconds), and any Savings Plan all lower the charge, and the credits are separate `Credit` line items. Add `resource_tags['user_workload']` to the grouping for each workload. Use `line_item_usage_start_date` with the times in `experiments.csv` to split a deployment's costs by experiment.
4. **Find the MicroVM costs.** MicroVMs can't be tagged, so check their rows' `line_item_resource_id`. If the IDs are MicroVM IDs, match them to `microvm-lifetimes.csv` and `microvms.jsonl` for each MicroVM's experiment. If they are image ARNs, the image tags apply. Either way, a MicroVM's baseline is billed for every second it runs: 1 vCPU and 2 GB for the 2048 MB deployment. Its lifetime times that baseline should match the bill's baseline usage. Burst vCPU time above the baseline appears only in the bill.
5. **Check the event functions.** For each function, `gbSeconds` in `event-usage.csv` should match the bill's GB-second usage, and `invocations` its requests. Lambda has billed the init phase since August 2025. Compare `billedSeconds` with `durationSeconds` and `initSeconds` to see whether the billed duration includes it.
6. **Include the costs the experiments add elsewhere,** or leave them out deliberately. These include CloudWatch Logs for the event functions' logs, data transfer for the responses, S3 for the MicroVM image sources and the CUR export, and MicroVM image storage, which costs $0.08 per GB-month whether or not anything runs. CUR has each one under its own service.

Don't call the tagged resources outside `run.sh` during the experiments, or the bill will mix those calls in. The pilot runs through `run.sh`, so `experiments.csv` records it.

## Results

Each experiment writes, in `history/<deployment>/<workload>/`:

- `<function>-<experiment>-0MBs-run<N>.csv` for each burst: every successful request's SAAF attributes and FaaS Runner's `roundTripTime`, `latency`, and `runtimeOverlap`, then averages by category (`newcontainer`, `uuid`, and `cpuInfo`).
- `<function>-<experiment>-0MBs-run<N>/`, with one JSON file for each successful request, holding the same attributes.
- `<function>-<experiment>-0MBs-COMBINED.csv`, for experiments with more than one burst: all of them together, with an `iteration` column.
- `<experiment>.log`, FaaS Runner's output, with each failed and timed-out request and its reason.

FaaS Runner stores every value as text, with commas replaced by semicolons so the CSVs stay valid. That includes nested ones like `cpuInfo`. Requests that failed or timed out are only in the log and `experiments.csv`.

## FaaS Runner Changes

`tools/experiment_caller.py`, `tools/experiment_orchestrator.py`, and `faas_runner.py` have four changes for these experiments:

- **Parsing.** Responses are parsed as JSON before `ast.literal_eval`. Six workloads return `true` or `false` (`correct`, `sync`, `keepAlive`, `disk`), which `literal_eval` rejects, so FaaS Runner would have counted every one of their requests as failed.
- **Headers.** A function file's `headersFile` names a JSON object of extra headers, read for every request. MicroVMs require the `X-aws-proxy-auth` header, and their tokens expire during long experiments.
- **Failures.** A request whose connection fails, or whose response has no SAAF attributes, such as a 429 when a deployment is throttled, is logged as `Run <thread>.<run> failed:` with the reason. The thread moves on to its next request. Before, a failed connection ended the thread, so a single one ended `sequential-0100`, and an error response was logged as successful, though it was never in the results.
- **Timeout.** An experiment's `timeout` is the number of seconds an HTTP request waits for its response, 0 for no limit. A request that times out fails, and FaaS Runner sends no more requests in that experiment and skips its remaining iterations. The function keeps running on the platform, and Lambda bills it until it finishes, so the timeout limits waiting rather than cost.
