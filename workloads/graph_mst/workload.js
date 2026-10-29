/**
 * graph_mst: minimum spanning tree with Kruskal's algorithm.
 *
 * Ported from graph_mst_2 in sebs_functions_dynamic.py, the pure Python version of
 * the SeBS graph-mst benchmark. Each thread builds the graph and gives every edge a
 * random weight from 1 to 100 in setup(). Each unit sorts the edges by weight and
 * joins components with a union-find, as the Python version did on every loop.
 */

const graph = require('./graph');
const { Random, derive } = require('./random');

function find(parent, i) {
    while (parent[i] !== i) {
        parent[i] = parent[parent[i]];
        i = parent[i];
    }
    return i;
}

module.exports = {
    units: (params) => params.loops,

    setup(params) {
        const { from, to } = graph.edges(params);
        const random = new Random(derive(params.seed, 0));
        const weight = new Int32Array(from.length);
        for (let i = 0; i < weight.length; i++) {
            weight[i] = random.int(1, 100);
        }
        return { size: params.size, from, to, weight };
    },

    unit({ size, from, to, weight }) {
        const order = new Int32Array(from.length);
        for (let i = 0; i < order.length; i++) {
            order[i] = i;
        }
        order.sort((x, y) => weight[x] - weight[y]);

        const parent = new Int32Array(size);
        for (let v = 0; v < size; v++) {
            parent[v] = v;
        }
        const rank = new Uint8Array(size);

        let edges = 0;
        let total = 0;
        for (let i = 0; i < order.length && edges < size - 1; i++) {
            const e = order[i];
            const x = find(parent, from[e]);
            const y = find(parent, to[e]);
            if (x !== y) {
                if (rank[x] < rank[y]) {
                    parent[x] = y;
                } else if (rank[x] > rank[y]) {
                    parent[y] = x;
                } else {
                    parent[y] = x;
                    rank[x]++;
                }
                edges++;
                total += weight[e];
            }
        }
        return [edges, total];
    },

    combine: (results) => ({ mstEdges: results[0][0], mstWeight: results[0][1] })
};
