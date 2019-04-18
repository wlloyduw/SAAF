/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package ibm;
import com.google.gson.*;
import faasinspector.Inspector;
import java.util.HashMap;

/**
 *
 * @author robertcordingly
 */
public class Hello {
    
    public static JsonObject main(JsonObject args) {
        //Collect data
        Inspector inspector = new Inspector();
        inspector.inspectAll();
        
        //Add custom message and finish the function
        inspector.addAttribute("message", "Hello " + args.getAsJsonPrimitive("name").getAsString() + "!");
        
        //Convert Inspector Hashmap to JsonObject
        JsonObject output = new JsonObject();
        HashMap<String, Object> results = inspector.finish();
        results.keySet().forEach((s) -> {
            output.addProperty(s, (String) results.get(s));
        });
        return output;
    }
    
}
