/**
 * dna_visualization: turning a DNA sequence into a 2D walk.
 *
 * Ported from dna_visualization (SeBS, using the squiggle package) and
 * dna_visualization_no_dependency in sebs_functions_dynamic.py. Each thread
 * generates a random sequence of a, c, g, and t in setup(). Each unit counts the
 * bases, as the Python version did, and computes the walk squiggle's default method
 * draws: A and C bump up and down by half a step, and G and T step up and down by
 * one. The walk's x and y coordinates fill two Float64Arrays of 2 * length + 1,
 * which setup() allocates once so the units do not spend their time on page faults.
 */

const { Random } = require('./random');

const BASES = 'acgt';

module.exports = {
    units: (params) => params.loops,

    setup(params) {
        const random = new Random(params.seed);
        const codes = Buffer.alloc(params.length);
        for (let i = 0; i < codes.length; i++) {
            codes[i] = BASES.charCodeAt(Math.floor(random.next() * 4));
        }
        return {
            sequence: codes.toString('latin1'),
            x: new Float64Array(2 * params.length + 1),
            y: new Float64Array(2 * params.length + 1)
        };
    },

    unit({ sequence, x, y }) {
        let a = 0, c = 0, g = 0, t = 0;
        let value = 0;

        for (let i = 0; i < sequence.length; i++) {
            const p = 2 * i + 1;
            x[p] = i + 0.5;
            x[p + 1] = i + 1;
            // Lowercase, so A and a are the same base.
            switch (sequence.charCodeAt(i) | 0x20) {
                case 97:
                    a++;
                    y[p] = value + 0.5;
                    break;
                case 99:
                    c++;
                    y[p] = value - 0.5;
                    break;
                case 103:
                    g++;
                    y[p] = value + 0.5;
                    value += 1;
                    break;
                case 116:
                    t++;
                    y[p] = value - 0.5;
                    value -= 1;
                    break;
                default:
                    y[p] = value;
            }
            y[p + 1] = value;
        }
        return [a, c, g, t, value];
    },

    combine: (results) => ({
        countA: results[0][0],
        countC: results[0][1],
        countG: results[0][2],
        countT: results[0][3],
        walkEnd: results[0][4]
    })
};
