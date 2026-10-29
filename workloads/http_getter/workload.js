/**
 * http_getter: HTTP GET requests.
 *
 * Ported from http_getter in sebs_functions_dynamic.py. Each unit is one GET of
 * url, and each thread sends its requests one after another, so threads is the
 * number of requests in flight. With keepAlive false, each request opens a new
 * connection, as Python's urlopen did, including the TLS handshake for https. With
 * keepAlive true, each thread reuses one connection.
 *
 * A request that fails or takes longer than timeout seconds counts in
 * failedRequests rather than failing the function. The default url,
 * checkip.amazonaws.com, returns the caller's public IP address, so responseSample
 * shows the address each environment's traffic leaves from. Point url at an
 * endpoint you own for large experiments.
 */

const http = require('http');
const https = require('https');
const { performance } = require('perf_hooks');

function get(url, agent, timeout) {
    return new Promise((resolve) => {
        const start = performance.now();
        const failed = () => resolve([0, 0, performance.now() - start, '']);
        const client = url.startsWith('https:') ? https : http;
        const request = client.get(url, { agent, timeout: timeout * 1000 }, (response) => {
            const chunks = [];
            response.on('data', (chunk) => chunks.push(chunk));
            response.on('error', failed);
            response.on('end', () => {
                const body = Buffer.concat(chunks);
                resolve([response.statusCode, body.length, performance.now() - start, body.toString('utf8', 0, 100).trim()]);
            });
        });
        request.on('timeout', () => request.destroy(new Error('Request timed out')));
        request.on('error', failed);
    });
}

function percentile(sorted, fraction) {
    return sorted.length > 0 ? Math.round(sorted[Math.floor(fraction * (sorted.length - 1))] * 100) / 100 : 0;
}

module.exports = {
    units: (params) => params.loops,

    setup(params) {
        if (!/^https?:\/\//.test(params.url)) {
            throw new Error('url must start with http:// or https://');
        }
        if (!params.keepAlive) {
            return false;
        }
        const client = params.url.startsWith('https:') ? https : http;
        return new client.Agent({ keepAlive: true, maxSockets: 1 });
    },

    unit: (agent, params) => get(params.url, agent, params.timeout),

    // Close the kept-alive connection, so it does not keep the thread running.
    teardown(agent) {
        if (agent) {
            agent.destroy();
        }
    },

    combine(results) {
        const succeeded = results.filter((result) => result[0] !== 0);
        const statusCodes = {};
        for (const [status] of succeeded) {
            statusCodes[status] = (statusCodes[status] || 0) + 1;
        }
        const latencies = Float64Array.from(succeeded, (result) => result[2]).sort();
        return {
            failedRequests: results.length - succeeded.length,
            statusCodes,
            bytesReceived: succeeded.reduce((total, result) => total + result[1], 0),
            latencyMin: percentile(latencies, 0),
            latencyMedian: percentile(latencies, 0.5),
            latencyP95: percentile(latencies, 0.95),
            latencyMax: percentile(latencies, 1),
            responseSample: succeeded.length > 0 ? succeeded[succeeded.length - 1][3] : ''
        };
    }
};
