package lambda;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import saaf.Inspector;
import saaf.Response;
import java.util.HashMap;

/**
 * uwt.lambda_test::handleRequest
 *
 * @author Wes Lloyd
 * @author Robert Cordingly
 */
public class Hello implements RequestHandler<Request, HashMap<String, Object>> {

    /**
     * Lambda Function Handler
     * 
     * @param request Request POJO with defined variables from Request.java
     * @param context 
     * @return HashMap that Lambda will automatically convert into JSON.
     */
    public HashMap<String, Object> handleRequest(Request request, Context context) {
        
        //Collect inital data.
        Inspector inspector = new Inspector();
        inspector.inspectAll();
        
        //Add custom message to FaaS Inspector.
        inspector.addAttribute("message", "Hello " + request.getName() 
                + "! This is an attributed added to the Inspector!");
        
        //Use and consome a response object. (OPTIONAL)
        Response response = new Response();
        response.setValue("Hello " + request.getName() 
                + "! This is from a response object!");
        
        inspector.consumeResponse(response);
        
        //Collect final information such as total runtime and cpu deltas.
        inspector.inspectCPUDelta();
        return inspector.finish();
    }
}
