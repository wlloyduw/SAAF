/**
 * thumbnailer: resizing an RGB image.
 *
 * Ported from thumbnailer_no_dependencies in sebs_functions_dynamic.py, the version
 * of the SeBS thumbnailer benchmark without Pillow or S3. Each thread generates the
 * same gradient image in setup(). Unit i resizes it to i / loops + 0.5 times its
 * size, so the sizes run from 0.5 to almost 1.5 times the original. Each unit
 * writes into a buffer setup() allocates once for the largest size, so the units
 * do not spend their time on page faults.
 *
 * filter "nearest" copies the nearest pixel, as the Python version did. "bilinear"
 * blends the 4 nearest pixels, which takes more arithmetic for each pixel.
 */

function generate(width, height) {
    const pixels = new Uint8Array(width * height * 3);
    let i = 0;
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            pixels[i++] = Math.floor(x * 255 / width);
            pixels[i++] = Math.floor(y * 255 / height);
            pixels[i++] = Math.floor((x + y) * 255 / (width + height));
        }
    }
    return pixels;
}

function nearest(source, width, height, newWidth, newHeight, resized) {
    let o = 0;
    for (let y = 0; y < newHeight; y++) {
        const row = Math.floor(y * height / newHeight) * width;
        for (let x = 0; x < newWidth; x++) {
            const s = (row + Math.floor(x * width / newWidth)) * 3;
            resized[o++] = source[s];
            resized[o++] = source[s + 1];
            resized[o++] = source[s + 2];
        }
    }
}

function bilinear(source, width, height, newWidth, newHeight, resized) {
    const xRatio = (width - 1) / Math.max(newWidth - 1, 1);
    const yRatio = (height - 1) / Math.max(newHeight - 1, 1);
    let o = 0;
    for (let y = 0; y < newHeight; y++) {
        const sy = y * yRatio;
        const y0 = Math.floor(sy);
        const y1 = Math.min(y0 + 1, height - 1);
        const fy = sy - y0;
        for (let x = 0; x < newWidth; x++) {
            const sx = x * xRatio;
            const x0 = Math.floor(sx);
            const x1 = Math.min(x0 + 1, width - 1);
            const fx = sx - x0;
            const i00 = (y0 * width + x0) * 3;
            const i01 = (y0 * width + x1) * 3;
            const i10 = (y1 * width + x0) * 3;
            const i11 = (y1 * width + x1) * 3;
            for (let channel = 0; channel < 3; channel++) {
                const top = source[i00 + channel] + (source[i01 + channel] - source[i00 + channel]) * fx;
                const bottom = source[i10 + channel] + (source[i11 + channel] - source[i10 + channel]) * fx;
                resized[o++] = Math.round(top + (bottom - top) * fy);
            }
        }
    }
}

module.exports = {
    units: (params) => params.loops,

    setup(params) {
        if (params.filter !== 'nearest' && params.filter !== 'bilinear') {
            throw new Error('filter must be "nearest" or "bilinear"');
        }
        return {
            original: generate(params.width, params.height),
            buffer: new Uint8Array(Math.floor(params.width * 1.5) * Math.floor(params.height * 1.5) * 3)
        };
    },

    unit({ original, buffer }, params, index) {
        const scale = index / params.loops + 0.5;
        const newWidth = Math.floor(params.width * scale);
        const newHeight = Math.floor(params.height * scale);
        const resize = params.filter === 'bilinear' ? bilinear : nearest;
        const resized = buffer.subarray(0, newWidth * newHeight * 3);
        resize(original, params.width, params.height, newWidth, newHeight, resized);

        let checksum = 0;
        for (let i = 0; i < resized.length; i += 4099) {
            checksum += resized[i];
        }
        return [newWidth, newHeight, resized.length, checksum];
    },

    combine: (results) => ({
        finalWidth: results[results.length - 1][0],
        finalHeight: results[results.length - 1][1],
        finalSize: results[results.length - 1][2],
        checksum: results.reduce((sum, result) => sum + result[3], 0)
    })
};
