/**
 * calc_service: random array writes and arithmetic.
 *
 * Ported from SAAF's calcs_service (Archives/calcs_service.zip) and calc_service in
 * sebs_functions_dynamic.py. Each loop picks calcs random slots in three operand
 * arrays, fills them with random numbers, then multiplies and divides them. With
 * large arrays the random slots miss the CPU caches. Each unit is one loop.
 */

const { Random, derive } = require('./random');

module.exports = {
    units: (params) => params.loops,

    setup: (params) => ({
        a: new Float64Array(params.calcs),
        b: new Float64Array(params.calcs),
        c: new Float64Array(params.calcs)
    }),

    unit({ a, b, c }, params, index) {
        const random = new Random(derive(params.seed, index));
        const calcs = params.calcs;
        let sum = 0;
        for (let i = 0; i < calcs; i++) {
            const j = Math.floor(random.next() * calcs);
            a[j] = Math.floor(random.next() * 99999);
            b[j] = Math.floor(random.next() * 99999);
            c[j] = 1 + Math.floor(random.next() * 99999);
            const mult = a[j] * b[j];
            sum += mult / c[j];
        }
        return sum;
    },

    combine: (results) => ({ checksum: results.reduce((sum, value) => sum + value, 0) })
};
