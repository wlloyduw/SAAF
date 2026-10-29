/**
 * csv_processor: column arithmetic over a table, as pandas would do it.
 *
 * Ported from csv_processor_no_dependencies in sebs_functions_dynamic.py, the
 * version of csv_processor without pandas or NumPy. Each loop generates four
 * columns of size random integers from 10 to 1000. Each of its calcs runs the
 * Python version's column operations: element-wise +, -, *, /, %, and sqrt, plus
 * sum, mean, min, and max. Each operation makes a new Float64Array, as each list
 * comprehension made a new list. Each unit is one loop.
 */

const { Random, derive } = require('./random');

function sum(column) {
    return column.reduce((total, value) => total + value, 0);
}

module.exports = {
    units: (params) => params.loops,

    unit(state, params, index) {
        const size = params.size;
        const random = new Random(derive(params.seed, index));
        const column = () => Float64Array.from({ length: size }, () => random.int(10, 1000));
        const A = column();
        const B = column();
        const C = column();
        const D = column();

        let checksum = 0;
        for (let calc = 0; calc < params.calcs; calc++) {
            let E = A.map((a, i) => a + B[i]);
            E = C.map((c, i) => c - D[i]);
            E = A.map((a, i) => a * B[i]);
            E = C.map((c) => c / 5);
            E = D.map((d) => d % 9);

            const sumA = sum(A);
            const meanB = sum(B) / size;
            const sqrtC = C.map(Math.sqrt);
            const minA = A.reduce((min, a) => (a < min ? a : min), Infinity);
            const maxB = B.reduce((max, b) => (b > max ? b : max), -Infinity);

            E = new Float64Array(size).fill(sumA);
            E = new Float64Array(size).fill(meanB);
            E = sqrtC;
            E = new Float64Array(size).fill(minA);
            E = new Float64Array(size).fill(maxB);
            checksum += sumA + meanB + sqrtC[calc % size] + minA + E[0];
        }
        return checksum;
    },

    combine: (results) => ({ checksum: results.reduce((total, value) => total + value, 0) })
};
