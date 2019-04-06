/**
 * Azure Functions Default Function
 *
 * This hander is used as a bridge to call the platform neutral
 * version in function.js. This script is put into the scr directory
 * when using publish.sh.
 *
 * @param context
 * @param req
 * @returns {Promise<void>}
 */
module.exports = async function(context, req) {
	context.res = {
		status: 200,
		body: (require('./function'))(req.body)
	};
};
