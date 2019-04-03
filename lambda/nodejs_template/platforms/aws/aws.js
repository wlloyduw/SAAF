/**
 * AWS Lambda Default Function
 *
 * @param event
 */
exports.handler = async (event) => {
	return (require('./function'))(event);
};