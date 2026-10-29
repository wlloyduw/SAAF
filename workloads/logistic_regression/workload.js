/**
 * logistic_regression: logistic regression trained by stochastic gradient descent.
 *
 * Ported from logistic_regression_parallel in sebs_functions_dynamic.py. The Python
 * version trained one model with threads that shared its weights under the GIL. Here
 * the samples are split into shards, each unit trains a model on one shard, and
 * combine() averages the models, so the result does not depend on the thread count.
 *
 * Every shard is drawn from the same true model: features are uniform from -1 to 1,
 * and each label is 1 with the probability the true model gives.
 */

const { Random, derive } = require('./random');

function sigmoid(z) {
    return 1 / (1 + Math.exp(-z));
}

module.exports = {
    units: (params) => params.shards,

    unit(state, params, index) {
        const features = params.features;
        const samples = Math.floor(params.samples / params.shards) + (index < params.samples % params.shards ? 1 : 0);

        const truth = new Random(params.seed);
        const trueWeights = Float64Array.from({ length: features }, () => truth.next() * 4 - 2);
        const trueBias = truth.next() * 2 - 1;

        const random = new Random(derive(params.seed, index));
        const x = new Float64Array(samples * features);
        const y = new Uint8Array(samples);
        for (let i = 0; i < samples; i++) {
            let z = trueBias;
            for (let j = 0; j < features; j++) {
                x[i * features + j] = random.next() * 2 - 1;
                z += trueWeights[j] * x[i * features + j];
            }
            y[i] = random.next() < sigmoid(z) ? 1 : 0;
        }

        // The last entry is the bias.
        const weights = new Float64Array(features + 1);
        for (let epoch = 0; epoch < params.epochs; epoch++) {
            for (let i = 0; i < samples; i++) {
                let z = weights[features];
                for (let j = 0; j < features; j++) {
                    z += weights[j] * x[i * features + j];
                }
                const step = params.learningRate * (y[i] - sigmoid(z));
                for (let j = 0; j < features; j++) {
                    weights[j] += step * x[i * features + j];
                }
                weights[features] += step;
            }
        }

        let correct = 0;
        for (let i = 0; i < samples; i++) {
            let z = weights[features];
            for (let j = 0; j < features; j++) {
                z += weights[j] * x[i * features + j];
            }
            correct += (z >= 0 ? 1 : 0) === y[i] ? 1 : 0;
        }
        return { weights: Array.from(weights), correct, samples };
    },

    combine(results, params) {
        const weights = new Array(params.features + 1).fill(0);
        let correct = 0;
        let samples = 0;
        for (const result of results) {
            result.weights.forEach((weight, j) => {
                weights[j] += weight / results.length;
            });
            correct += result.correct;
            samples += result.samples;
        }
        return {
            weights: weights.slice(0, params.features),
            bias: weights[params.features],
            accuracy: correct / samples
        };
    }
};
