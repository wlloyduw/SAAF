/**
 * Platform-neutral workload function.
 * Each platform handler calls this function: platforms/aws_event/index.js for Lambda
 * event functions, and the index.js servers from web_template and microvm_template.
 *
 * The workload runs between inspectAll() and inspectAllDeltas(), so userRuntime and
 * the CPU and memory deltas cover the workload and nothing else.
 *
 * Requests run one at a time. A request that arrives while another is running waits
 * here before its Inspector starts, so CPU and memory deltas belong to one request.
 *
 * @param request Parsed request. Fields named in workload.json's defaults are the
 *                workload's parameters, and every other field is ignored.
 * @param context Request context. The Lambda context's awsRequestId, or the
 *                requestId web_template's server sets, is reported as requestId.
 * @returns SAAF attribute object from Inspector.finish().
 */
let queue = Promise.resolve();

module.exports = function (request, context) {
    const result = queue.then(() => execute(request || {}, context || {}));
    queue = result.catch(() => {});
    return result;
};

async function execute(request, context) {

    //Import the module and collect data
    const inspector = new (require('./Inspector'))();
    inspector.inspectAll();

    const requestId = context.awsRequestId || context.requestId;
    if (requestId) {
        inspector.addAttribute('requestId', requestId);
    }

    //Run the workload and add its parameters and results
    const attributes = await require('./runner').run(request);
    for (const [key, value] of Object.entries(attributes)) {
        inspector.addAttribute(key, value);
    }

    inspector.inspectAllDeltas();
    return inspector.finish();
}
