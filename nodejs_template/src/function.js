
/**
 * Define your FaaS Function here.
 * Each platform handler will call and pass parameters to this function.
 *
 * @param request A JSON object provided by the platform handler.
 * @param context A platform specific object used to communicate with the platform.
 * @returns A JSON object to use as a response.
 */
module.exports = function(request, context) {
        
    //Import the module and collect data
    const inspector = new (require('./Inspector'))();
    inspector.inspectAll();

    //Add custom message and finish the function
    if (typeof request.name !== 'undefined' && request.name !== null) {
        inspector.addAttribute("message", "Hello " + request.name + "!");
    } else {
        inspector.addAttribute("message", "Hello World!");
    }
    
    inspector.inspectAllDeltas();
    //inspector.pushS3("saafdump", context)
    return inspector.finish();
};