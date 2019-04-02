/**
 * AWS Lambda Default Handler
 *
 * @param event
 */
exports.handler = async (event) => {
	return (require('./function'))(event);
};