/**
 * Graphs for graph_bfs, graph_mst, and graph_pagerank.
 *
 * Graphs are undirected, and every node has degree 10, as in the Python versions:
 *
 *   tree:      igraph.Graph.Tree(size, 10), which the Python versions used. The
 *              children of node p are 10p + 1 to 10p + 10.
 *   barabasi:  A Barabasi-Albert graph like igraph.Graph.Barabasi(size, 10), which
 *              SeBS uses. Each new node links to 10 earlier nodes, picked with
 *              probability proportional to their degree plus one.
 */

const { Random } = require('./random');

const DEGREE = 10;

function treeEdges(size) {
    const from = new Int32Array(Math.max(size - 1, 0));
    const to = new Int32Array(from.length);
    for (let child = 1; child < size; child++) {
        from[child - 1] = Math.floor((child - 1) / DEGREE);
        to[child - 1] = child;
    }
    return { from, to };
}

function barabasiEdges(size, random) {
    const from = new Int32Array(size * DEGREE);
    const to = new Int32Array(size * DEGREE);

    // pool holds every node once, plus once more for each edge it is on, so a
    // uniform pick from pool is proportional to degree plus one.
    const pool = new Int32Array(size * (2 * DEGREE + 1));
    const picked = new Int32Array(DEGREE);
    let edges = 0;
    let poolSize = 0;
    pool[poolSize++] = 0;

    for (let node = 1; node < size; node++) {
        const links = Math.min(node, DEGREE);
        let count = 0;
        while (count < links) {
            const target = pool[Math.floor(random.next() * poolSize)];
            let repeat = false;
            for (let i = 0; i < count && !repeat; i++) {
                repeat = picked[i] === target;
            }
            if (!repeat) {
                picked[count++] = target;
            }
        }
        for (let i = 0; i < links; i++) {
            from[edges] = node;
            to[edges] = picked[i];
            edges++;
            pool[poolSize++] = picked[i];
            pool[poolSize++] = node;
        }
        pool[poolSize++] = node;
    }
    return { from: from.subarray(0, edges), to: to.subarray(0, edges) };
}

/**
 * Generate the edges of the graph named by params.graph, with params.size nodes.
 *
 * @returns {from, to} Int32Arrays with one entry per edge.
 */
function edges(params) {
    if (params.graph === 'tree') {
        return treeEdges(params.size);
    }
    if (params.graph === 'barabasi') {
        return barabasiEdges(params.size, new Random(params.seed));
    }
    throw new Error('graph must be "tree" or "barabasi"');
}

/**
 * Store an undirected graph in compressed sparse row form. The neighbors of node v
 * are targets[offsets[v]] up to, but not including, targets[offsets[v + 1]].
 */
function csr(size, { from, to }) {
    const offsets = new Int32Array(size + 1);
    for (let i = 0; i < from.length; i++) {
        offsets[from[i] + 1]++;
        offsets[to[i] + 1]++;
    }
    for (let v = 0; v < size; v++) {
        offsets[v + 1] += offsets[v];
    }

    const targets = new Int32Array(from.length * 2);
    const next = offsets.slice(0, size);
    for (let i = 0; i < from.length; i++) {
        targets[next[from[i]]++] = to[i];
        targets[next[to[i]]++] = from[i];
    }
    return { size, offsets, targets };
}

module.exports = { edges, csr };
