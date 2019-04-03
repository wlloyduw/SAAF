/**
 * IBM Cloud Functions/OpenWhisk Default Function
 *
 * @param params
 * @returns {{message: string}}
 */
function main(params) {
	return (require('./function'))(params);
}

exports.main = main;