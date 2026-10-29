/**
 * sleeper: waits without using the CPU.
 *
 * Ported from sleeper in sebs_functions_dynamic.py. It is a control rather than a
 * CPU-bound workload: its runtime is the platform's overhead plus time seconds, and
 * comparing its cost shows what each paradigm charges for time a function spends
 * waiting.
 */

module.exports = {
    units: () => 1,

    unit: (state, params) => new Promise((resolve) => setTimeout(resolve, params.time * 1000)),

    combine: () => ({})
};
