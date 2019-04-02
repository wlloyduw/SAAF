/**
 * IBM Cloud Functions Default Handler
 *
 * @param params
 * @returns {{message: string}}
 */
function main(params) {
	return (require('./yourFunction'))(params);
}