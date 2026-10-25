/**
 * Call the platform-neutral function once, without starting the HTTP server.
 * Execute from this directory with: node local.js
 */
const payload = { name: 'Bob' };
const result = require('../src/function')(payload, null);
console.log(JSON.stringify(result, null, 2));
