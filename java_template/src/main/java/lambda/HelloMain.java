package lambda;

import com.amazonaws.services.lambda.runtime.ClientContext;
import com.amazonaws.services.lambda.runtime.CognitoIdentity;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.LambdaLogger;
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
public class HelloMain implements RequestHandler<HashMap<String, Object>, HashMap<String, Object>> {

    /**
     * Lambda Function Handler
     * 
     * @param request Hashmap containing request JSON attributes.
     * @param context 
     * @return HashMap that Lambda will automatically convert into JSON.
     */
    public HashMap<String, Object> handleRequest(HashMap<String, Object> request, Context context) {
        
        //Collect inital data.
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
    
    public static void main (String[] args)
    {
        Context c = new Context() {
            @Override
            public String getAwsRequestId() {
                return "";
            }

            @Override
            public String getLogGroupName() {
                return "";
            }

            @Override
            public String getLogStreamName() {
                return "";
            }

            @Override
            public String getFunctionName() {
                return "";
            }

            @Override
            public String getFunctionVersion() {
                return "";
            }

            @Override
            public String getInvokedFunctionArn() {
                return "";
            }

            @Override
            public CognitoIdentity getIdentity() {
                return null;
            }

            @Override
            public ClientContext getClientContext() {
                return null;
            }

            @Override
            public int getRemainingTimeInMillis() {
                return 0;
            }

            @Override
            public int getMemoryLimitInMB() {
                return 0;
            }

            @Override
            public LambdaLogger getLogger() {
                return new LambdaLogger() {
                    @Override
                    public void log(String string) {
                        System.out.println("LOG:" + string);
                    }
                };
            }
        };
        
        HelloMain hm = new HelloMain();
        
        // Create a request hash map
        HashMap req = new HashMap();
        
        // Grab the name from the cmdline from arg 0
        String name = (args.length > 0 ? args[0] : "");

        // Load the name into the request hashmap
        req.put("name", name);
        
        // Report name to stdout
        System.out.println("cmd-line param name=" + req.get("name"));
        
        // Run the function
        HashMap resp = hm.handleRequest(req, c);        
        
        // Print out function result
        System.out.println("function result:" + resp.toString());
        
        
        
    }
}
