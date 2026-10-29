/**
 * json_flattener: flattening a nested JSON object into dotted keys.
 *
 * Ported from json_flattener in sebs_functions_dynamic.py. Each thread generates an
 * object breadth keys wide and depth levels deep, with a random 10-character string
 * at each leaf, in setup(). Each unit flattens it the way the Python version did,
 * copying each child's keys into its parent with Object.assign, as dict.update did.
 * The work is mostly string concatenation, hashing, and garbage collection.
 */

const { Random } = require('./random');

const CHARACTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';

function generate(level, params, random) {
    if (level >= params.depth) {
        let leaf = '';
        for (let i = 0; i < 10; i++) {
            leaf += CHARACTERS[Math.floor(random.next() * CHARACTERS.length)];
        }
        return leaf;
    }
    const node = {};
    for (let i = 0; i < params.breadth; i++) {
        node['key_' + i] = generate(level + 1, params, random);
    }
    return node;
}

function flatten(object, parentKey) {
    const items = {};
    for (const key of Object.keys(object)) {
        const value = object[key];
        const newKey = parentKey ? parentKey + '.' + key : key;
        if (typeof value === 'object') {
            Object.assign(items, flatten(value, newKey));
        } else {
            items[newKey] = value;
        }
    }
    return items;
}

module.exports = {
    units: (params) => params.loops,

    setup: (params) => generate(0, params, new Random(params.seed)),

    unit: (nested) => Object.keys(flatten(nested, '')).length,

    combine: (results) => ({ flatKeys: results[0] })
};
