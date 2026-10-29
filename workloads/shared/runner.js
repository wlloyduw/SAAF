/**
 * Runs the workload in workload.js with the parameters from a request.
 *
 * A workload's work is divided into units, such as one loop, one matrix product, or
 * one image row. workload.js exports:
 *
 *   units(params)                 The number of units.
 *   setup(params)                 Optional. Builds state the units share, such as a
 *                                 graph. Runs once in each thread.
 *   unit(state, params, index)    Runs one unit and returns its result. Can return a
 *                                 Promise.
 *   teardown(state, params)       Optional. Runs once in each thread after its units,
 *                                 even if one fails, such as to delete files.
 *   combine(results, params)      Reduces the results, in unit order, to the
 *                                 attributes the function reports.
 *
 * With threads set to 1, every unit runs on the main thread. Otherwise each worker
 * thread runs every threads-th unit, starting at its own index, and the results are
 * put back in unit order. Units draw their data from the seed and their index, so
 * the results are the same for any number of threads.
 */

const os = require('os');
const path = require('path');
const { performance } = require('perf_hooks');
const { Worker } = require('worker_threads');

const config = require('./workload.json');

/**
 * Read the workload's parameters from a request. Every field in workload.json's
 * defaults is a parameter. A field missing from the request takes its default, and
 * strings from query parameters are converted to the default's type.
 */
function readParams(request) {
    const params = {};
    for (const [key, fallback] of Object.entries(config.defaults)) {
        let value = request[key];
        if (value === undefined || value === null || value === '') {
            value = fallback;
        } else if (typeof fallback === 'number') {
            value = Number(value);
            if (!Number.isFinite(value)) {
                throw new Error(key + ' must be a number');
            }
        } else if (typeof fallback === 'boolean') {
            value = value === true || value === 'true';
        } else if (typeof fallback === 'string') {
            value = String(value);
        }
        params[key] = value;
    }
    return params;
}

/**
 * Run the units first, first + step, first + 2 * step, ... below units.
 *
 * @returns The results of those units, and the time in ms to set up and run them.
 */
async function runUnits(workload, params, first, step, units) {
    let start = performance.now();
    const state = workload.setup ? await workload.setup(params) : undefined;
    const setupRuntime = performance.now() - start;

    start = performance.now();
    const results = [];
    let computeRuntime;
    try {
        for (let index = first; index < units; index += step) {
            results.push(await workload.unit(state, params, index));
        }
        computeRuntime = performance.now() - start;
    } finally {
        if (workload.teardown) {
            await workload.teardown(state, params);
        }
    }
    return { results, setupRuntime, computeRuntime };
}

function runWorker(params, first, step, units) {
    return new Promise((resolve, reject) => {
        const worker = new Worker(path.join(__dirname, 'worker.js'), { workerData: { params, first, step, units } });
        worker.once('message', resolve);
        worker.once('error', reject);
        worker.once('exit', (code) => {
            if (code !== 0) {
                reject(new Error('Worker stopped with exit code ' + code));
            }
        });
    });
}

/**
 * Run the workload and return the attributes to report.
 *
 * workload:         The name of the workload.
 * threads:          The number of threads used. 0 in the request means one per vCPU,
 *                   and it is never more than units.
 * units:            The number of units the work was divided into.
 * (parameters)      Every parameter, with the value used.
 * (results)         The attributes from the workload's combine().
 * setupRuntime:     The longest time in ms any thread spent in setup().
 * computeRuntime:   The longest time in ms any thread spent running units.
 * workloadRuntime:  The time in ms from starting the threads to having every result.
 */
async function run(request) {
    const workload = require('./workload');
    const params = readParams(typeof request === 'object' && !Array.isArray(request) ? request : {});

    const units = workload.units(params);
    if (!Number.isInteger(units) || units < 1) {
        throw new Error('The parameters give ' + units + ' units of work. There must be at least 1.');
    }

    let threads = Math.floor(params.threads ?? 1);
    if (threads === 0) {
        threads = os.availableParallelism();
    }
    threads = Math.max(1, Math.min(threads, units));

    const start = performance.now();
    const parts = threads === 1
        ? [await runUnits(workload, params, 0, 1, units)]
        : await Promise.all(Array.from({ length: threads }, (_, first) => runWorker(params, first, threads, units)));
    const workloadRuntime = performance.now() - start;

    const results = new Array(units);
    parts.forEach((part, first) => {
        part.results.forEach((result, i) => {
            results[first + i * threads] = result;
        });
    });

    return {
        workload: config.name,
        ...params,
        threads: threads,
        units: units,
        ...workload.combine(results, params),
        setupRuntime: Math.round(Math.max(...parts.map((part) => part.setupRuntime))),
        computeRuntime: Math.round(Math.max(...parts.map((part) => part.computeRuntime))),
        workloadRuntime: Math.round(workloadRuntime)
    };
}

module.exports = { run, runUnits };
