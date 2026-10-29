/**
 * nqueens: counting every solution to the n-queens puzzle.
 *
 * Backtracking with bitmasks: integer and bitwise operations, recursion, and
 * branches that are hard to predict, with a working set that fits in registers.
 * Each unit places the queens in the first two rows, one of n * n ways, and counts
 * the solutions that follow. Invalid placements end at once.
 *
 * correct reports whether solutions matches the known count, for n up to 18.
 */

const SOLUTIONS = [1, 1, 0, 0, 2, 10, 4, 40, 92, 352, 724, 2680, 14200, 73712, 365596, 2279184, 14772512,
    95815104, 666090624];

function count(columns, left, right, all) {
    if (columns === all) {
        return 1;
    }
    let solutions = 0;
    let free = all & ~(columns | left | right);
    while (free !== 0) {
        const bit = free & -free;
        free ^= bit;
        solutions += count(columns | bit, ((left | bit) << 1) & all, (right | bit) >> 1, all);
    }
    return solutions;
}

module.exports = {
    units(params) {
        if (!Number.isInteger(params.n) || params.n < 1 || params.n > 30) {
            throw new Error('n must be an integer from 1 to 30');
        }
        return params.n * params.n;
    },

    unit(state, { n }, index) {
        if (n === 1) {
            return 1;
        }
        const all = (1 << n) - 1;
        const first = 1 << Math.floor(index / n);
        const second = 1 << (index % n);
        if (second & (first | (first << 1) | (first >> 1))) {
            return 0;
        }
        const left = (((first << 1) | second) << 1) & all;
        const right = ((first >> 1) | second) >> 1;
        return count(first | second, left, right, all);
    },

    combine(results, params) {
        const solutions = results.reduce((sum, value) => sum + value, 0);
        const attributes = { solutions };
        if (params.n < SOLUTIONS.length) {
            attributes.correct = solutions === SOLUTIONS[params.n];
        }
        return attributes;
    }
};
