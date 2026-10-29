/**
 * Worker thread started by runner.js. Runs its share of the workload's units and
 * posts their results back.
 */

const { parentPort, workerData } = require('worker_threads');
const { runUnits } = require('./runner');

const { params, first, step, units } = workerData;
runUnits(require('./workload'), params, first, step, units).then((part) => parentPort.postMessage(part));
