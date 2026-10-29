/**
 * AWS Lambda handler for the workloads' event functions.
 * Calls the workload function in function.js with the request's JSON.
 *
 * aws lambda invoke sends the request's JSON as the event. A function URL sends an
 * event that describes the HTTP request, with the request's JSON as text in its body,
 * base64-encoded when isBase64Encoded is true. Lambda returns the result as the
 * HTTP response's JSON body.
 *
 * @param event The request's JSON, or a function URL event.
 * @param context The Lambda context object.
 */
exports.handler = async (event, context) => {
	let request = event;
	if (event && event.requestContext && event.requestContext.http) {
		const body = event.isBase64Encoded ? Buffer.from(event.body || '', 'base64').toString() : event.body;
		request = body ? JSON.parse(body) : {};
	}
	return (require('./function'))(request, context);
};
