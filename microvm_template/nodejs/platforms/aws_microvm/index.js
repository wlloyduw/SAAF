/**
 * AWS Lambda MicroVM server.
 *
 * Lambda starts this file while it builds the MicroVM image, snapshots it, and
 * sends requests for each MicroVM to port 8080. Requests to the lifecycle hooks
 * are answered here. Every other request is passed to function.js: fields from
 * the JSON body and query string are copied onto the request, and the SAAF
 * attributes it returns are sent back as JSON.
 *
 * function.js runs synchronously, so requests are handled one at a time and CPU
 * and memory deltas belong to one request.
 */

const fs = require('fs');
const http = require('http');
const handle = require('./function');

const PORT = 8080;
const HOOKS = '/aws/lambda-microvms/runtime/v1/';
const RESERVED = new Set(['method', 'path', 'query', 'headers', 'body']);

function readBody(req) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        req.on('data', (chunk) => chunks.push(chunk));
        req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
        req.on('error', reject);
    });
}

function applyFields(target, source) {
    Object.keys(source).forEach((key) => {
        if (!RESERVED.has(key) && !(key in target)) {
            target[key] = source[key];
        }
    });
}

function sendJson(res, statusCode, payload) {
    const body = JSON.stringify(payload);
    res.writeHead(statusCode, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    res.end(body);
}

const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const query = Object.fromEntries(url.searchParams);
    const text = await readBody(req);

    // Lambda calls /ready during the image build, before the snapshot, and /run
    // when a MicroVM starts from the snapshot, with that MicroVM's ID.
    if (url.pathname === HOOKS + 'ready') {
        sendJson(res, 200, {});
        return;
    }
    if (url.pathname === HOOKS + 'run') {
        let microvmId = '';
        try {
            microvmId = JSON.parse(text).microvmId || '';
        } catch (err) {
        }
        fs.writeFileSync('/tmp/microvm-id', microvmId);
        sendJson(res, 200, {});
        return;
    }

    let body;
    try {
        body = text ? JSON.parse(text) : {};
    } catch (err) {
        sendJson(res, 400, { error: 'Request body is not valid JSON' });
        return;
    }

    const request = {
        method: req.method,
        path: url.pathname,
        query: query,
        headers: req.headers,
        body: body
    };
    if (body && typeof body === 'object' && !Array.isArray(body)) {
        applyFields(request, body);
    }
    applyFields(request, query);

    try {
        sendJson(res, 200, await handle(request, {}));
    } catch (err) {
        sendJson(res, 500, { error: String(err) });
    }
});

server.listen(PORT, '0.0.0.0', () => {
    console.log('SAAF MicroVM server listening on port ' + PORT);
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
