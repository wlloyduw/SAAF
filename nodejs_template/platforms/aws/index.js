/**
 * AWS Lambda Default Function
 * Calls the function defined in /src/function.js
 *
 * This hander is used as a bridge to call the platform neutral
 * version in function.js. This script is put into the scr directory
 * when using publish.sh.
 *
 * The handler is async because the nodejs24.x runtime and later do not
 * support callback handlers. function.js can return its result or a Promise.
 *
 * @param event JSON provided by AWS.
 * @param context The Lambda context object.
 */
exports.handler = async (event, context) => {
	return (require('./function'))(event, context);
};
