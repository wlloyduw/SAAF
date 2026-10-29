/**
 * graph_pagerank: PageRank by power iteration.
 *
 * Ported from graph_page_rank_2 in sebs_functions_dynamic.py, the pure Python
 * version of the SeBS graph-pagerank benchmark. The Python version spent most of
 * its time generating the graph loops times and then checked every pair of nodes
 * for an edge. Here each thread builds the graph once in setup(), and each unit
 * computes PageRank over the graph's edges with a damping factor of 0.85.
 *
 * Each unit runs exactly iterations iterations, with no early stop on convergence,
 * so every unit does the same work.
 */

const graph = require('./graph');

const DAMPING = 0.85;

module.exports = {
    units: (params) => params.loops,

    setup: (params) => graph.csr(params.size, graph.edges(params)),

    unit({ size, offsets, targets }, params) {
        let rank = new Float64Array(size).fill(1 / size);
        let next = new Float64Array(size);
        const share = new Float64Array(size);

        for (let iteration = 0; iteration < params.iterations; iteration++) {
            for (let v = 0; v < size; v++) {
                const degree = offsets[v + 1] - offsets[v];
                share[v] = degree > 0 ? rank[v] / degree : 0;
            }
            for (let v = 0; v < size; v++) {
                let sum = 0;
                for (let e = offsets[v]; e < offsets[v + 1]; e++) {
                    sum += share[targets[e]];
                }
                next[v] = (1 - DAMPING) / size + DAMPING * sum;
            }
            [rank, next] = [next, rank];
        }

        let maxNode = 0;
        for (let v = 1; v < size; v++) {
            if (rank[v] > rank[maxNode]) {
                maxNode = v;
            }
        }
        return [maxNode, rank[maxNode]];
    },

    combine: (results) => ({ maxRankNode: results[0][0], maxRank: results[0][1] })
};
