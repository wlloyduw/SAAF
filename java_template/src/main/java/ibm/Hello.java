package ibm;
import com.google.gson.*;
import saaf.Inspector;
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
        String name = "World";
        JsonPrimitive input = args.getAsJsonPrimitive("name");
        if (input != null) {
            name = input.getAsString();
        }
        inspector.addAttribute("message", "Hello " + name + "!");
        
        //Calculate CPU deltas.
        inspector.inspectAllDeltas();
        
        //Convert Inspector Hashmap to JsonObject
        JsonObject output = new JsonObject();
        HashMap<String, Object> results = inspector.finish();
        results.keySet().forEach((s) -> {
            output.addProperty(s, String.valueOf(results.get(s)));
        });
        return output;
    }
}
