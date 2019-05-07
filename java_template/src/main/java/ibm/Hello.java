package ibm;
import com.google.gson.*;
import faasinspector.Inspector;
import java.util.HashMap;

/**
 * @author Robert Cordingly
 */
public class Hello {
   
    /**
     * IBM Cloud Functions default handler.
     * 
     * @param args JsonObject of input Json.
     * @return JsonObject of output.
     */
    public static JsonObject main(JsonObject args) {
        //Collect data
        Inspector inspector = new Inspector();
        inspector.inspectAll();
        
        //Add custom message and finish the function
        inspector.addAttribute("message", "Hello " + args.getAsJsonPrimitive("name").getAsString() + "!");
        
        //Calculate CPU deltas.
        inspector.inspectCPUDelta();
        
        //Convert Inspector Hashmap to JsonObject
        JsonObject output = new JsonObject();
        HashMap<String, Object> results = inspector.finish();
        results.keySet().forEach((s) -> {
            output.addProperty(s, (String) results.get(s));
        });
        return output;
    }
    
}
