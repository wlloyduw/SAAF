/**
 * binary_trees: allocating and walking complete binary trees.
 *
 * Millions of small, short-lived objects, so the work is allocation and V8's
 * garbage collector. Each unit builds a tree of the given depth, counts its nodes,
 * and drops it. Each thread has its own heap and collector.
 *
 * correct reports whether nodes is trees * (2^(depth + 1) - 1).
 */

class TreeNode {
    constructor(left, right) {
        this.left = left;
        this.right = right;
    }
}

function build(depth) {
    return depth === 0 ? new TreeNode(null, null) : new TreeNode(build(depth - 1), build(depth - 1));
}

function check(node) {
    return node.left === null ? 1 : 1 + check(node.left) + check(node.right);
}

module.exports = {
    units: (params) => params.trees,

    unit: (state, params) => check(build(params.depth)),

    combine(results, params) {
        const nodes = results.reduce((sum, value) => sum + value, 0);
        return { nodes, correct: nodes === params.trees * (2 ** (params.depth + 1) - 1) };
    }
};
