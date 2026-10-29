/**
 * graph_bfs: breadth-first search of a graph.
 *
 * Ported from graph_bfs_2 in sebs_functions_dynamic.py, the pure Python version of
 * the SeBS graph-bfs benchmark. Each thread builds the graph and the search's
 * visited and queue arrays in setup(), and each unit is one search from node 0.
 *
 * On the tree graph, nodes are numbered level by level, so the search reads memory
 * in order. On the barabasi graph it jumps around.
 */

const graph = require('./graph');

module.exports = {
    units: (params) => params.loops,

    setup: (params) => ({
        ...graph.csr(params.size, graph.edges(params)),
        visited: new Uint8Array(params.size),
        queue: new Int32Array(params.size)
    }),

    unit({ offsets, targets, visited, queue }) {
        visited.fill(0);
        let head = 0;
        let tail = 0;
        let checksum = 0;

        visited[0] = 1;
        queue[tail++] = 0;
        while (head < tail) {
            const node = queue[head++];
            checksum = (Math.imul(checksum, 31) + node) | 0;
            for (let e = offsets[node]; e < offsets[node + 1]; e++) {
                const neighbor = targets[e];
                if (!visited[neighbor]) {
                    visited[neighbor] = 1;
                    queue[tail++] = neighbor;
                }
            }
        }
        return [tail, checksum];
    },

    combine: (results) => ({ visited: results[0][0], checksum: results[0][1] })
};
