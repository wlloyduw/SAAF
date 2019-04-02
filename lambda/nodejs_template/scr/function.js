
/**
 * Define your FaaS Function here.
 * Each platform handler will call and pass parameters to this function.
 *
 * @param A JSON object provided by the platform handler.
 * @returns A JSON object to use as a reponse.
 */
module.exports = function(request) {
        
    //Run FaaS Inspector to create a reponse JSON object.
    const inspector = new (require('./Inspector'))();
    let response = inspector.profileVM();
    
    //Hello World!
    let name = request.name;
    response['name'] = name;
    response['message'] = 'Hello ' + name + '!';
    
    return response;
};