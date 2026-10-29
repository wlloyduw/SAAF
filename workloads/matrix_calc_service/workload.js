/**
 * matrix_calc_service: dense integer matrix multiplication.
 *
 * Ported from matrix_calc_service (NumPy) and matrix_calc_service_2 (pure Python) in
 * sebs_functions_dynamic.py. Each loop generates two size x size matrices of random
 * integers from 0 to 999, multiplies them, then multiplies the product by the second
 * matrix again, as np.matmul and np.dot did. Each unit is one loop.
 *
 * Matrices are Float64Arrays multiplied in i-k-j order. Every entry stays below
 * 2^53 for sizes up to about 2900, so the products are exact.
 */

const { Random, derive } = require('./random');

function randomMatrix(size, random) {
    const matrix = new Float64Array(size * size);
    for (let i = 0; i < matrix.length; i++) {
        matrix[i] = Math.floor(random.next() * 1000);
    }
    return matrix;
}

function multiply(a, b, size) {
    const c = new Float64Array(size * size);
    for (let i = 0; i < size; i++) {
        const row = i * size;
        for (let k = 0; k < size; k++) {
            const aik = a[row + k];
            const column = k * size;
            for (let j = 0; j < size; j++) {
                c[row + j] += aik * b[column + j];
            }
        }
    }
    return c;
}

module.exports = {
    units: (params) => params.loops,

    unit(state, params, index) {
        const random = new Random(derive(params.seed, index));
        const matrix1 = randomMatrix(params.size, random);
        const matrix2 = randomMatrix(params.size, random);
        const matrix3 = multiply(matrix1, matrix2, params.size);
        const val = multiply(matrix3, matrix2, params.size);

        let checksum = 0;
        for (let i = 0; i < val.length; i++) {
            checksum += val[i] % 1000003;
        }
        return checksum;
    },

    combine: (results) => ({ checksum: results.reduce((sum, value) => sum + value, 0) })
};
