
/**
 * Define your FaaS Function here.
 * Each platform handler will call and pass parameters to this function.
 *
 * @param request A JSON object provided by the platform handler.
 * @returns A JSON object to use as a response.
 */
module.exports = function(request) {
        
    //Import the module and collect data
    const inspector = new (require('./Inspector'))();
    inspector.inspectAll();
    inspector.addTimeStamp("frameworkRuntime");

    //Add custom message and finish the function
    inspector.addAttribute("message", "Hello " + request.name + "!");
    
    inspector.inspectCPUDelta()
    return inspector.finish();
};