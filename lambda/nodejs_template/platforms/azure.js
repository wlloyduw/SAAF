/**
 * Azure Functions Default Function
 *
 * @param context
 * @param req
 * @returns {Promise<void>}
 */
module.exports = async function(context, req) {
	context.res = {
		status: 200,
		body: (require('./function'))(req)
	};
};
