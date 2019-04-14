package lambda;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import faasinspector.Inspector;
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
        
        //Collect data
        Inspector inspector = new Inspector();
        inspector.inspectCPU();
        inspector.inspectContainer();
        inspector.inspectLinux();
        inspector.inspectPlatform();
        inspector.addTimeStamp("frameworkRuntime");
        
        //Add custom message and finish the function
        inspector.addAttribute("message", "Hello " + request.getName() + "!");
        return inspector.finish();
    }
}
