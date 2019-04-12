/**
 * Execute this function to test your function locally.
 * Execute with: node local.js
 *
 * Required Node Modules:
 * npm install uuid 
 *
 * @param params
 * @returns {{message: string}}
 */
function main(params) {
	return (require('../src/function'))(params);
}

console.log(main({"name": "bob"}));