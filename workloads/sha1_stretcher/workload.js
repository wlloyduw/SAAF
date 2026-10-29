/**
 * sha1_stretcher: key stretching by repeated hashing.
 *
 * Ported from sha1_stretcher in sebs_functions_dynamic.py, which hashed its input
 * loops times, feeding each digest into the next hash. A hash chain cannot be split
 * between threads, so here the loops are divided among chains independent chains,
 * and each unit is one chain. Chain 0 starts from input, and chain c starts from
 * input + ":" + c.
 *
 * With chains set to 1, digest is the digest the Python version returned. With more
 * chains, it is the hash of the chains' hex digests joined in order.
 *
 * Each hash is of a 20-byte digest, so the time is mostly Node's per-call overhead
 * into OpenSSL rather than SHA-1 itself. crypto.hash() is the one-shot API, which
 * has less overhead than crypto.createHash().
 */

const crypto = require('crypto');

module.exports = {
    units: (params) => params.chains,

    unit(state, params, index) {
        const length = Math.floor(params.loops / params.chains) + (index < params.loops % params.chains ? 1 : 0);
        let digest = Buffer.from(index === 0 ? params.input : params.input + ':' + index);
        for (let i = 0; i < length; i++) {
            digest = crypto.hash(params.algorithm, digest, 'buffer');
        }
        return digest.toString('hex');
    },

    combine: (results, params) => ({
        digest: results.length === 1
            ? results[0]
            : crypto.hash(params.algorithm, results.join(''), 'hex')
    })
};
