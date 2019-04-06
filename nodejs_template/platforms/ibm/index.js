/**
 * IBM Cloud Functions/OpenWhisk Default Function
 *
 * This hander is used as a bridge to call the platform neutral
 * version in function.js. This script is put into the scr directory
 * when using publish.sh.
 *
 * @param params
 * @returns {{message: string}}
 */
function main(params) {
	return (require('./function'))(params);
}

exports.main = main;