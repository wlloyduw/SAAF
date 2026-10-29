/**
 * Seeded pseudo-random numbers for the workloads.
 *
 * Every workload draws its data from its seed parameter, so each platform runs
 * exactly the same work and returns the same checksums.
 */

class Random {

    /**
     * @param seed A 32-bit integer.
     */
    constructor(seed) {
        this.state = seed >>> 0;
    }

    /**
     * A number from 0 up to, but not including, 1. Uses mulberry32.
     */
    next() {
        this.state = (this.state + 0x6D2B79F5) >>> 0;
        let t = this.state;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }

    /**
     * An integer from min to max, including both, like Python's random.randint.
     */
    int(min, max) {
        return min + Math.floor(this.next() * (max - min + 1));
    }
}

/**
 * Derive the seed for one unit of work from the workload's seed, so each unit gets
 * its own data whichever thread runs it.
 */
function derive(seed, index) {
    let h = (seed ^ Math.imul(index + 1, 0x9E3779B9)) >>> 0;
    h = Math.imul(h ^ (h >>> 16), 0x85EBCA6B);
    h = Math.imul(h ^ (h >>> 13), 0xC2B2AE35);
    return (h ^ (h >>> 16)) >>> 0;
}

module.exports = { Random, derive };
