/**
 * File helpers for the disk workloads: disk_writer, disk_write_and_process, and
 * zipper with disk set.
 */

const fs = require('fs');
const path = require('path');
const { threadId } = require('worker_threads');

/**
 * A path in params.dir that no other thread or process uses, such as
 * /tmp/saaf-123-2-text0.txt in thread 2 of process 123.
 */
function scratchPath(params, name) {
    return path.join(params.dir, 'saaf-' + process.pid + '-' + threadId + '-' + name);
}

/**
 * Write data to a new file, and flush it to the disk with fsync before closing it
 * when sync is set.
 */
function writeFile(file, data, sync) {
    const fd = fs.openSync(file, 'w');
    try {
        let offset = 0;
        while (offset < data.length) {
            offset += fs.writeSync(fd, data, offset, data.length - offset);
        }
        if (sync) {
            fs.fsyncSync(fd);
        }
    } finally {
        fs.closeSync(fd);
    }
}

/**
 * Delete files, ignoring any that do not exist.
 */
function removeFiles(...files) {
    for (const file of files) {
        fs.rmSync(file, { force: true });
    }
}

module.exports = { scratchPath, writeFile, removeFiles };
