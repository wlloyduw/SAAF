/**
 * disk_write_and_process: reading a file with command-line tools.
 *
 * Ported from disk_write_and_process in sebs_functions_dynamic.py. setup() writes a
 * file of size MiB of "wow cool nice " repeated to dir, as the Python version did.
 * Each unit then runs the Python version's 5 commands on the file: wc -w, wc -l,
 * base64, sha1sum, and cat. Each command writes its output to a file that is
 * deleted afterward, so each unit reads the file 5 times and writes about 2.4 times
 * its size.
 *
 * mode "subprocess" runs the commands with spawnSync, as the Python version did, so
 * the time includes starting 5 processes. It needs wc, base64, sha1sum, and cat on
 * the PATH. mode "node" does the same reads, work, and writes inside Node.js, and
 * writes base64 in 76-character lines as GNU base64 does. Both modes report the
 * same results on Linux.
 */

const crypto = require('crypto');
const fs = require('fs');
const { spawnSync } = require('child_process');
const { scratchPath, writeFile, removeFiles } = require('./files');

// 57 bytes encode to exactly one 76-character line of base64.
const CHUNK = 57 * 16384;

/**
 * Read a file in chunks of CHUNK bytes, passing each to fn before reading the next.
 */
function eachChunk(file, fn) {
    const fd = fs.openSync(file, 'r');
    const buffer = Buffer.allocUnsafe(CHUNK);
    try {
        let length;
        do {
            length = 0;
            let read;
            while (length < CHUNK && (read = fs.readSync(fd, buffer, length, CHUNK - length, null)) > 0) {
                length += read;
            }
            if (length > 0) {
                fn(buffer.subarray(0, length));
            }
        } while (length === CHUNK);
    } finally {
        fs.closeSync(fd);
    }
}

/**
 * Write output to a new file the way a command would write to stdout.
 */
function withOutput(file, fn) {
    const fd = fs.openSync(file, 'w');
    try {
        return fn((data) => {
            const buffer = typeof data === 'string' ? Buffer.from(data) : data;
            let offset = 0;
            while (offset < buffer.length) {
                offset += fs.writeSync(fd, buffer, offset, buffer.length - offset);
            }
            return buffer.length;
        });
    } finally {
        fs.closeSync(fd);
    }
}

const inNode = {
    words(input, output) {
        let words = 0;
        let inWord = false;
        eachChunk(input, (chunk) => {
            for (let i = 0; i < chunk.length; i++) {
                const c = chunk[i];
                const space = c === 32 || (c >= 9 && c <= 13);
                if (!space && !inWord) {
                    words++;
                }
                inWord = !space;
            }
        });
        withOutput(output, (write) => write(words + '\n'));
        return words;
    },

    lines(input, output) {
        let lines = 0;
        eachChunk(input, (chunk) => {
            for (let i = chunk.indexOf(10); i !== -1; i = chunk.indexOf(10, i + 1)) {
                lines++;
            }
        });
        withOutput(output, (write) => write(lines + '\n'));
        return lines;
    },

    base64(input, output) {
        return withOutput(output, (write) => {
            let bytes = 0;
            eachChunk(input, (chunk) => {
                const encoded = chunk.toString('base64');
                const lines = [];
                for (let i = 0; i < encoded.length; i += 76) {
                    lines.push(encoded.slice(i, i + 76));
                }
                bytes += write(lines.join('\n') + '\n');
            });
            return bytes;
        });
    },

    sha1(input, output) {
        const hash = crypto.createHash('sha1');
        eachChunk(input, (chunk) => hash.update(chunk));
        const digest = hash.digest('hex');
        withOutput(output, (write) => write(digest + '  ' + input + '\n'));
        return digest;
    },

    cat(input, output) {
        return withOutput(output, (write) => {
            let bytes = 0;
            eachChunk(input, (chunk) => {
                bytes += write(chunk);
            });
            return bytes;
        });
    }
};

/**
 * Run a command with its output written to a file, as the Python version did.
 */
function run(command, args, output) {
    const fd = fs.openSync(output, 'w');
    try {
        const result = spawnSync(command, args, { stdio: ['ignore', fd, 'pipe'] });
        if (result.error) {
            throw result.error;
        }
        if (result.status !== 0) {
            throw new Error(command + ' exited with status ' + result.status + ': ' + result.stderr);
        }
    } finally {
        fs.closeSync(fd);
    }
}

const inSubprocess = {
    words(input, output) {
        run('wc', ['-w', input], output);
        return parseInt(fs.readFileSync(output, 'utf8').trim(), 10);
    },

    lines(input, output) {
        run('wc', ['-l', input], output);
        return parseInt(fs.readFileSync(output, 'utf8').trim(), 10);
    },

    base64(input, output) {
        run('base64', [input], output);
        return fs.statSync(output).size;
    },

    sha1(input, output) {
        run('sha1sum', [input], output);
        return fs.readFileSync(output, 'utf8').slice(0, 40);
    },

    cat(input, output) {
        run('cat', [input], output);
        return fs.statSync(output).size;
    }
};

module.exports = {
    units: (params) => params.loops,

    setup(params) {
        if (params.mode !== 'subprocess' && params.mode !== 'node') {
            throw new Error('mode must be "subprocess" or "node"');
        }
        const input = scratchPath(params, 'readwrite.txt');
        try {
            writeFile(input, Buffer.alloc(Math.floor(params.size * 1048576), 'wow cool nice '), false);
        } catch (err) {
            removeFiles(input);
            throw err;
        }
        return { input, output: scratchPath(params, 'out.log') };
    },

    unit({ input, output }, params) {
        const commands = params.mode === 'node' ? inNode : inSubprocess;
        const results = [];
        for (const command of ['words', 'lines', 'base64', 'sha1', 'cat']) {
            try {
                results.push(commands[command](input, output));
            } finally {
                removeFiles(output);
            }
        }
        return results;
    },

    teardown: ({ input }) => removeFiles(input),

    combine: (results) => ({
        words: results[0][0],
        lines: results[0][1],
        base64Bytes: results[0][2],
        sha1: results[0][3],
        catBytes: results[0][4]
    })
};
