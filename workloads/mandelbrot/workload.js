/**
 * mandelbrot: escape-time rendering of the Mandelbrot set.
 *
 * Floating-point multiply and add in a tight loop over a few registers, with
 * almost no memory traffic. Each unit is one row of a width x height grid over
 * -2 to 0.5 on the real axis and -1.25 to 1.25 on the imaginary axis. A point is
 * inside the set if it has not escaped after iterations iterations.
 */

module.exports = {
    units: (params) => params.height,

    unit(state, { width, height, iterations }, row) {
        const ci = -1.25 + 2.5 * (row + 0.5) / height;
        let inside = 0;
        let total = 0;
        for (let column = 0; column < width; column++) {
            const cr = -2 + 2.5 * (column + 0.5) / width;
            let zr = 0;
            let zi = 0;
            let i = 0;
            while (i < iterations && zr * zr + zi * zi <= 4) {
                const t = zr * zr - zi * zi + cr;
                zi = 2 * zr * zi + ci;
                zr = t;
                i++;
            }
            inside += i === iterations ? 1 : 0;
            total += i;
        }
        return [inside, total];
    },

    combine: (results) => ({
        insidePoints: results.reduce((sum, result) => sum + result[0], 0),
        totalIterations: results.reduce((sum, result) => sum + result[1], 0)
    })
};
