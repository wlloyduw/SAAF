/**
 * disk_writer: writing files and deleting them.
 *
 * Ported from disk_writer in sebs_functions_dynamic.py. Each unit writes a file of
 * size MiB to dir and deletes it. The file is "1234567890" repeated, as in the
 * Python version, whose default of 80 MiB matches its 23 doublings of that string.
 *
 * Without sync, a write usually stays in the page cache, and the file is deleted
 * before it reaches the disk, so the time is mostly the file system and memory
 * copies. With sync, each file is flushed to the disk with fsync before it closes.
 */

const { scratchPath, writeFile, removeFiles } = require('./files');

module.exports = {
    units: (params) => params.loops,

    setup: (params) => Buffer.alloc(Math.floor(params.size * 1048576), '1234567890'),

    unit(data, params, index) {
        const file = scratchPath(params, 'text' + index + '.txt');
        try {
            writeFile(file, data, params.sync);
        } finally {
            removeFiles(file);
        }
        return data.length;
    },

    combine: (results) => ({ bytesWritten: results.reduce((total, bytes) => total + bytes, 0) })
};
