/**
 * log_parser: parsing and summarizing web server access logs.
 *
 * A common serverless job: regular expressions, string splitting, number parsing,
 * and hash maps. Each thread generates the same log of lines lines in setup(), in
 * the combined log format with a response time in ms at the end. Each unit splits
 * the log, matches every line, and summarizes it: server errors, bytes sent,
 * distinct clients, the busiest path, and the 95th percentile response time.
 */

const { Random } = require('./random');

const METHODS = ['GET', 'GET', 'GET', 'GET', 'POST', 'POST', 'PUT', 'DELETE'];
const PATHS = ['/', '/index.html', '/login', '/search', '/api/users', '/api/orders', '/api/cart', '/api/products',
    '/static/app.js', '/static/style.css', '/images/logo.png', '/images/banner.jpg'];
const STATUSES = [200, 200, 200, 200, 200, 200, 200, 201, 204, 301, 304, 304, 400, 401, 403, 404, 404, 500, 502, 503];
const AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0',
    'curl/8.9.1',
    'python-requests/2.32.3'
];
const REFERRERS = ['-', 'https://www.example.com/', 'https://www.example.com/search', 'https://news.example.org/'];

const LINE = /^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) ([^ ?"]+)(?:\?[^ "]*)? (\S+)" (\d{3}) (\d+) "([^"]*)" "([^"]*)" (\d+(?:\.\d+)?)$/;

function pick(list, random) {
    return list[Math.floor(random.next() * list.length)];
}

function pad(value) {
    return value < 10 ? '0' + value : String(value);
}

module.exports = {
    units: (params) => params.loops,

    setup(params) {
        const random = new Random(params.seed);
        const lines = new Array(params.lines);
        for (let i = 0; i < params.lines; i++) {
            const client = random.int(0, 4999);
            const ip = '10.' + (client >> 8) + '.' + (client & 255) + '.' + random.int(1, 254);
            const seconds = Math.floor(i * 86400 / params.lines);
            const time = '29/Oct/2026:' + pad(Math.floor(seconds / 3600)) + ':' + pad(Math.floor(seconds / 60) % 60) + ':'
                + pad(seconds % 60) + ' +0000';
            const query = random.next() < 0.5 ? '?id=' + random.int(1, 100000) : '';
            const latency = (random.next() * random.next() * 2000).toFixed(1);
            lines[i] = ip + ' - - [' + time + '] "' + pick(METHODS, random) + ' ' + pick(PATHS, random) + query
                + ' HTTP/1.1" ' + pick(STATUSES, random) + ' ' + random.int(0, 50000) + ' "' + pick(REFERRERS, random)
                + '" "' + pick(AGENTS, random) + '" ' + latency;
        }
        return lines.join('\n');
    },

    unit(log) {
        const clients = new Set();
        const paths = new Map();
        const latencies = [];
        let serverErrors = 0;
        let bytes = 0;

        for (const line of log.split('\n')) {
            const match = LINE.exec(line);
            if (match === null) {
                continue;
            }
            clients.add(match[1]);
            paths.set(match[4], (paths.get(match[4]) || 0) + 1);
            const status = parseInt(match[6], 10);
            if (status >= 500) {
                serverErrors++;
            }
            bytes += parseInt(match[7], 10);
            latencies.push(parseFloat(match[10]));
        }

        let topPath = '';
        let topCount = 0;
        for (const [path, count] of paths) {
            if (count > topCount) {
                topPath = path;
                topCount = count;
            }
        }
        const sorted = Float64Array.from(latencies).sort();
        const p95Latency = sorted.length > 0 ? sorted[Math.floor(0.95 * (sorted.length - 1))] : 0;

        return [latencies.length, serverErrors, bytes, clients.size, topPath, p95Latency];
    },

    combine: (results) => ({
        parsedLines: results[0][0],
        serverErrors: results[0][1],
        bytesSent: results[0][2],
        distinctClients: results[0][3],
        topPath: results[0][4],
        p95Latency: results[0][5]
    })
};
