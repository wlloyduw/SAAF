# Lambda Web deployment

`publish.sh` and `run.sh` in this directory call the platform scripts in `../platforms/aws_web`. Settings live in `config.json`.

```bash
./publish.sh
./run.sh
./run.sh '{"name":"Ada"}'
```

`publish.sh` refreshes `../platforms/aws_web/.build` from `../src` and `../platforms/aws_web/index.js`, then runs `aws lambda-web deploy`. The endpoint URL is written to `endpoint.url` on success. That file is gitignored.

`run.sh` POSTs JSON to the endpoint and prints the response body. It uses `ENDPOINT_URL`, then `endpoint_url` in `config.json`, then `endpoint.url`, then `aws lambda-web get-web-function-endpoint`.

`local.js` calls `src/function.js` once in this process. `local.sh` starts the HTTP server on `localhost:3000`.

Platform scripts can also be run directly. The first argument is the directory they should treat as the working location, which is how the Jupyter platform scripts take their path:

```bash
../platforms/aws_web/build.sh ../platforms/aws_web
DRY_RUN=1 ../platforms/aws_web/publish.sh ../platforms/aws_web
../platforms/aws_web/run.sh ../platforms/aws_web '{"name":"Ada"}'
```

The AWS CLI must provide `aws lambda-web`. Check with `aws lambda-web help`. `jq` and `curl` are required. See the [template README](../README.md) for the config fields and the SAAF call sequence.
