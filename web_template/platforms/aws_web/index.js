/**
 * AWS Lambda Web Function bridge.
 *
 * Lambda loads this file and expects it to listen on the host and port in
 * AWS_LAMBDA_HTTP_ENDPOINT. Each request is parsed and passed to the
 * platform-neutral function in function.js, which owns SAAF collection.
 *
 * Local runs do not receive that variable. The fallback below listens on
 * localhost:3000 and records that address so SAAF can report the platform
 * as Local.
 */

const fs = require('fs');
const http = require('http');
const path = require('path');
const { URL } = require('url');

const RESERVED = new Set(['method', 'path', 'query', 'headers', 'body', 'requestId']);
const BODY_LIMIT = 1024 * 1024;

function userFunction() {
    if (fs.existsSync(path.join(__dirname, 'function.js'))) {
        return require('./function');
    }
    return require('../../src/function');
}

const handle = userFunction();

if (!process.env.AWS_LAMBDA_HTTP_ENDPOINT) {
    process.env.AWS_LAMBDA_HTTP_ENDPOINT = 'localhost:3000';
}

function listenAddress() {
    const endpoint = process.env.AWS_LAMBDA_HTTP_ENDPOINT;
    const separator = endpoint.lastIndexOf(':');
    if (separator === -1) {
        return { host: endpoint, port: 3000 };
    }
    let host = endpoint.slice(0, separator);
    if (host.startsWith('[') && host.endsWith(']')) {
        host = host.slice(1, -1);
    }
    const port = Number(endpoint.slice(separator + 1));
    return { host: host, port: Number.isFinite(port) ? port : 3000 };
}

function applyFields(target, source) {
    if (!source || typeof source !== 'object' || Array.isArray(source)) {
        return;
    }
    Object.keys(source).forEach((key) => {
        if (!RESERVED.has(key) && !Object.prototype.hasOwnProperty.call(target, key)) {
            target[key] = source[key];
        }
    });
}

function readBody(req) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        let size = 0;
        req.on('data', (chunk) => {
            size += chunk.length;
            if (size > BODY_LIMIT) {
                const error = new Error('Request body exceeds 1 MB');
                error.statusCode = 413;
                reject(error);
                req.destroy();
            } else {
                chunks.push(chunk);
            }
        });
        req.on('end', () => resolve(Buffer.concat(chunks)));
        req.on('error', reject);
    });
}

function buildRequest(req, rawBody) {
    const url = new URL(req.url || '/', 'http://localhost');
    const query = {};
    url.searchParams.forEach((value, key) => {
        query[key] = value;
    });

    let body = null;
    if (rawBody.length > 0) {
        const text = rawBody.toString('utf8');
        const type = String(req.headers['content-type'] || '');
        const trimmed = text.trim();
        const looksLikeJson = type.includes('json') || trimmed.startsWith('{') || trimmed.startsWith('[');
        if (looksLikeJson) {
            try {
                body = JSON.parse(text);
            } catch (err) {
                const error = new Error('Request body is not valid JSON');
                error.statusCode = 400;
                throw error;
            }
        } else {
            body = text;
        }
    }

    const request = {
        method: req.method,
        path: url.pathname,
        query: query,
        headers: req.headers,
        body: body,
        requestId: req.headers['lambda-web-request-id'] || null
    };
    applyFields(request, body);
    applyFields(request, query);
    return request;
}

function sendJson(res, statusCode, payload) {
    const body = JSON.stringify(payload);
    res.writeHead(statusCode, {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': Buffer.byteLength(body),
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    });
    res.end(body);
}

const { host, port } = listenAddress();

const server = http.createServer(async (req, res) => {
    if (req.method === 'OPTIONS') {
        res.writeHead(204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        });
        res.end();
        return;
    }

    try {
        const rawBody = await readBody(req);
        const request = buildRequest(req, rawBody);
        const context = {
            requestId: request.requestId,
            platform: 'AWS Lambda Web'
        };
        const result = await Promise.resolve(handle(request, context));
        if (result == null || typeof result !== 'object') {
            sendJson(res, 500, { error: 'Function returned no SAAF attributes' });
            return;
        }
        sendJson(res, 200, result);
    } catch (err) {
        const statusCode = err && err.statusCode ? err.statusCode : 500;
        sendJson(res, statusCode, { error: err && err.message ? err.message : String(err) });
    }
});

server.on('clientError', (err, socket) => {
    socket.end('HTTP/1.1 400 Bad Request\r\n\r\n');
});

server.on('error', (err) => {
    console.error(err);
    process.exit(1);
});

server.listen(port, host, () => {
    console.log('SAAF web function listening on ' + host + ':' + port);
});

process.on('SIGTERM', () => {
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(0), 500).unref();
});
