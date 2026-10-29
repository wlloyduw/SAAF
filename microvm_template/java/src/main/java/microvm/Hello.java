package microvm;

import saaf.Inspector;
import saaf.Response;
import java.util.HashMap;

/**
 * microvm.Hello::handleRequest
 *
 * The java_template lambda.Hello function. Server.java calls it for each request,
 * so it does not use the Lambda runtime's RequestHandler or Context.
 *
 * @author Wes Lloyd
 * @author Robert Cordingly
 */
public class Hello {

    /**
     * MicroVM Function Handler
     *
     * @param request Hashmap containing request JSON attributes.
     * @param context Request context passed by Server.java.
     * @return HashMap that Server.java converts into JSON.
     */
    public HashMap<String, Object> handleRequest(HashMap<String, Object> request, HashMap<String, Object> context) {

        //Collect initial data.
        Inspector inspector = new Inspector();
        inspector.inspectAll();

        //****************START FUNCTION IMPLEMENTATION*************************

        //Add custom key/value attribute to SAAF's output. (OPTIONAL)
        inspector.addAttribute("message", "Hello " + request.get("name")
                + "! This is a custom attribute added as output from SAAF!");

        //Create and populate a separate response object for function output. (OPTIONAL)
        Response response = new Response();
        response.setValue("Hello " + request.get("name")
                + "! This is from a response object!");

        inspector.consumeResponse(response);

        //****************END FUNCTION IMPLEMENTATION***************************

        //Collect final information such as total runtime and cpu deltas.
        inspector.inspectAllDeltas();
        return inspector.finish();
    }
}
