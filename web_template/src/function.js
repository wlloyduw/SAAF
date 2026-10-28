/**
 * Platform-neutral Web Function.
 * platforms/aws_web/index.js forwards each HTTP request here.
 *
 * @param request Parsed HTTP request. JSON body fields are copied onto this
 *                object, so a body of {"name":"Ada"} is available as request.name.
 *                request.method, request.path, request.query, request.headers,
 *                and request.body are also set.
 * @param context Request context. context.requestId is the lambda-web-request-id
 *                header when Lambda sends one.
 * @returns SAAF attribute object from Inspector.finish().
 */
module.exports = function (request, context) {

    //Import the module and collect data
    const inspector = new (require('./Inspector'))();
    inspector.inspectAll();

    request = request || {};
    context = context || {};

    if (request.method) {
        inspector.addAttribute('httpMethod', request.method);
    }
    if (request.path) {
        inspector.addAttribute('httpPath', request.path);
    }
    if (request.requestId || context.requestId) {
        inspector.addAttribute('requestId', request.requestId || context.requestId);
    }

    //Add custom message and finish the function
    if (typeof request.name !== 'undefined' && request.name !== null) {
        inspector.addAttribute('message', 'Hello ' + request.name + '!');
    } else {
        inspector.addAttribute('message', 'Hello World!');
    }

    inspector.inspectAllDeltas();
    return inspector.finish();
};
