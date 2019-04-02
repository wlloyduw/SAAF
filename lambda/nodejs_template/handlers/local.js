/**
 * A Local Handler
 *
 * @param params
 * @returns {{message: string}}
 */
function main(params) {
	console.log((require('./yourFunction'))(params));
}

main();