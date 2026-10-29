/**
 * zipper: DEFLATE compression of files.
 *
 * Ported from zipper in sebs_functions_dynamic.py, which wrote files to /tmp and
 * zipped them loops times. Each thread generates the files in setup(). Each unit
 * compresses one file once with Node's zlib, on the calling thread, using the raw
 * DEFLATE that zip archives use, so there are loops * files units.
 *
 * With disk false, the files stay in memory, so the work is the compression
 * itself. With disk true, as in the Python version, setup() writes the files to
 * dir, and each unit reads its file from there and writes the compressed file back
 * before deleting it.
 *
 * data "text" fills each file with random words, which compress about as well as
 * logs or prose. "digits" repeats "1234567890" as the Python version did, which
 * compresses far more easily.
 */

const fs = require('fs');
const zlib = require('zlib');
const { scratchPath, writeFile, removeFiles } = require('./files');
const { Random, derive } = require('./random');

const WORDS = [
    'the', 'of', 'and', 'to', 'in', 'is', 'for', 'on', 'with', 'as', 'by', 'at', 'from', 'that', 'this', 'it',
    'function', 'request', 'response', 'server', 'client', 'memory', 'runtime', 'container', 'instance', 'region',
    'lambda', 'event', 'invoke', 'timeout', 'error', 'warning', 'started', 'finished', 'duration', 'billed',
    'cold', 'warm', 'start', 'latency', 'throughput', 'cpu', 'thread', 'worker', 'queue', 'cache', 'disk', 'network',
    'user', 'session', 'token', 'header', 'payload', 'status', 'value', 'result', 'record', 'batch', 'stream', 'file'
];

function generate(params, file) {
    const bytes = Math.floor(params.size * 1048576);
    if (params.data === 'digits') {
        return Buffer.alloc(bytes, '1234567890');
    }
    if (params.data !== 'text') {
        throw new Error('data must be "text" or "digits"');
    }

    const random = new Random(derive(params.seed, file));
    const buffer = Buffer.alloc(bytes);
    let offset = 0;
    while (offset < bytes) {
        offset += buffer.write(WORDS[Math.floor(random.next() * WORDS.length)], offset, 'latin1');
        if (offset < bytes) {
            buffer[offset++] = random.next() < 0.1 ? 10 : 32;
        }
    }
    return buffer;
}

module.exports = {
    units: (params) => params.loops * params.files,

    // Returns the files' contents, or with disk set, the paths they were written to.
    setup(params) {
        const files = [];
        try {
            for (let file = 0; file < params.files; file++) {
                const data = generate(params, file);
                if (params.disk) {
                    files.push(scratchPath(params, 'text' + file + '.txt'));
                    writeFile(files[file], data, false);
                } else {
                    files.push(data);
                }
            }
        } catch (err) {
            if (params.disk) {
                removeFiles(...files);
            }
            throw err;
        }
        return files;
    },

    unit(files, params, index) {
        const file = files[index % params.files];
        if (!params.disk) {
            return zlib.deflateRawSync(file, { level: params.level }).length;
        }
        const zip = scratchPath(params, 'zip' + index + '.zip');
        try {
            const compressed = zlib.deflateRawSync(fs.readFileSync(file), { level: params.level });
            writeFile(zip, compressed, false);
            return compressed.length;
        } finally {
            removeFiles(zip);
        }
    },

    teardown(files, params) {
        if (params.disk) {
            removeFiles(...files);
        }
    },

    combine(results, params) {
        const compressedBytes = results.reduce((total, value) => total + value, 0);
        const inputBytes = results.length * Math.floor(params.size * 1048576);
        return { compressedBytes, compressionRatio: inputBytes / compressedBytes };
    }
};
