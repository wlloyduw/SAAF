/**
 * IBM Cloud Functions Default Function
 *
 * @param params
 * @returns {{message: string}}
 */
function main(params) {
	return (require('./function'))(params);
}