
/**
 * Define your FaaS Function here.
 * Each platform handler will call and pass parameters to this function.
 *
 * @param request A JSON object provided by the platform handler.
 * @returns A JSON object to use as a response.
 */
module.exports = function(request) {
        
    //Run FaaS Inspector and collect information about container and CPU.
    const inspector = new (require('./Inspector'))();
    inspector.inspectContainer();
    inspector.inspectCPU();
    inspector.inspectPlatform();
        
    //Hello World!
    let name = request.name;
    inspector.attributes['name'] = name;
    inspector.attributes['message'] = 'Hello ' + name + '!';
    
    return inspector.finish();
};