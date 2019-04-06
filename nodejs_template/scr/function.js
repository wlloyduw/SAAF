
/**
 * Define your FaaS Function here.
 * Each platform handler will call and pass parameters to this function.
 *
 * @param request A JSON object provided by the platform handler.
 * @returns A JSON object to use as a response.
 */
module.exports = function(request) {
        
    //Run FaaS Inspector and collect information about container, CPU, and platform.
    const inspector = new (require('./Inspector'))();
    inspector.inspectContainer();
    inspector.inspectCPU();
    inspector.inspectPlatform();
        
    //Get a command from input and execute the command.
    let command = request.command;
    if (command == null) command = "env";
    const { execSync } = require('child_process');
    let child = execSync(command, { encoding : 'utf8' });
    let results = "STDOUT: " + child;
    
    //Append attributes to FaaS Inspector and finish inspecting.
    inspector.attributes['command'] = command;
    inspector.attributes['results'] = results;
    return inspector.finish();
};