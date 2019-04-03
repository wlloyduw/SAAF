/**
 * Execute this function to test your function locally.
 *
 * Required Node Modules:
 * npm install uuid 
 *
 * @param params
 * @returns {{message: string}}
 */
function main(params) {
	return (require('../scr/function'))(params);
}

console.log(main({"name": "bob"}));