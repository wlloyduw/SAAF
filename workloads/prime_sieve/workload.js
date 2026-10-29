/**
 * prime_sieve: counting the primes up to limit with a segmented sieve of Eratosthenes.
 *
 * Strided writes over a byte array, so the work depends on the cache and memory
 * more than the other workloads. The sieve only stores odd numbers: index k is
 * 2k + 1. Each unit sieves segmentSize odd numbers, which should fit in the L2
 * cache, using the odd primes up to the square root of limit that setup() finds.
 *
 * correct reports whether primes matches the known count when limit is a power of 10
 * or 2 billion.
 */

const PRIMES = { 10: 4, 100: 25, 1000: 168, 10000: 1229, 100000: 9592, 1000000: 78498, 10000000: 664579,
    100000000: 5761455, 1000000000: 50847534, 2000000000: 98222287, 10000000000: 455052511 };

// The number of odd numbers from 1 to limit.
function odds(limit) {
    return Math.floor((limit + 1) / 2);
}

module.exports = {
    units: (params) => Math.ceil(odds(params.limit) / params.segmentSize),

    setup(params) {
        const root = Math.floor(Math.sqrt(params.limit));
        const composite = new Uint8Array(root + 1);
        const primes = [];
        for (let p = 3; p <= root; p += 2) {
            if (!composite[p]) {
                primes.push(p);
                for (let m = p * p; m <= root; m += 2 * p) {
                    composite[m] = 1;
                }
            }
        }
        return { primes: Int32Array.from(primes), segment: new Uint8Array(params.segmentSize) };
    },

    unit({ primes, segment }, params, index) {
        const low = index * params.segmentSize;
        const high = Math.min(low + params.segmentSize, odds(params.limit));
        const length = high - low;
        segment.fill(0, 0, length);

        for (let i = 0; i < primes.length; i++) {
            const p = primes[i];
            // The first odd multiple of p that is at least p * p and in this segment.
            let start = p * p;
            const lowest = 2 * low + 1;
            if (start < lowest) {
                start = lowest + (p - lowest % p) % p;
                if (start % 2 === 0) {
                    start += p;
                }
            }
            for (let k = (start - 1) / 2 - low; k < length; k += p) {
                segment[k] = 1;
            }
        }

        let primeCount = 0;
        for (let k = 0; k < length; k++) {
            primeCount += segment[k] === 0 ? 1 : 0;
        }
        // 1 is not prime.
        return low === 0 ? primeCount - 1 : primeCount;
    },

    combine(results, params) {
        // The sieve only counts odd primes, so add 2.
        const primes = results.reduce((sum, value) => sum + value, 0) + (params.limit >= 2 ? 1 : 0);
        const attributes = { primes };
        if (PRIMES[params.limit] !== undefined) {
            attributes.correct = primes === PRIMES[params.limit];
        }
        return attributes;
    }
};
