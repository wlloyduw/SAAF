/**
 * AWS Lambda Web Function server.
 *
 * Lambda starts this file and sends requests to the address in
 * AWS_LAMBDA_HTTP_ENDPOINT. Fields from the JSON body and query string are
 * copied onto the request passed to function.js, and the SAAF attributes it
 * returns are sent back as JSON.
 */

const http = require('http');
const handle = require('./function');

const RESERVED = new Set(['method', 'path', 'query', 'headers', 'body', 'requestId']);

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

    let body;
    try {
        const text = await readBody(req);
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
        body: body,
        requestId: req.headers['lambda-web-request-id']
    };
    if (body && typeof body === 'object' && !Array.isArray(body)) {
        applyFields(request, body);
    }
    applyFields(request, query);

    try {
        sendJson(res, 200, await handle(request, { requestId: request.requestId }));
    } catch (err) {
        sendJson(res, 500, { error: String(err) });
    }
});

const endpoint = process.env.AWS_LAMBDA_HTTP_ENDPOINT;
const separator = endpoint.lastIndexOf(':');
server.listen(Number(endpoint.slice(separator + 1)), endpoint.slice(0, separator), () => {
    console.log('SAAF web function listening on ' + endpoint);
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
