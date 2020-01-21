package lambda;

import com.google.gson.*;
import saaf.Inspector;
import java.util.UUID;
import java.io.InputStream;
import java.util.HashMap;


/**
 * Helper functions for creating functions on AWS Lambda
 * 
 * @author Robert Cordingly
 */
public class Helpers {
    private Helpers() {}

    /**
     * Push your inspector results to a S3 bucket.
     * 
     * @param inspector
     * @param bucketName
     */
    public static void s3Push(Inspector inspector, String bucketName) {
        /*
        String uuid = UUID.randomUUID().toString();

        //Convert Inspector Hashmap to JsonObject
        JsonObject output = new JsonObject();
        HashMap<String, Object> results = inspector.finish();
        results.keySet().forEach((s) -> {
            output.addProperty(s, String.valueOf(results.get(s)));
        });
        String jsonString = output.getAsString();

        byte[] bytes = jsonString.getBytes(StandardCharsets.UTF_8); 
        InputStream is = new ByteArrayInputStream(bytes); 
        ObjectMetadata meta = new ObjectMetadata(); 
        meta.setContentLength(bytes.length); 
        meta.setContentType("application/json");
        
        // Create new file on S3
        AmazonS3 s3Client = AmazonS3ClientBuilder.standard().build(); s3Client.putObject(bucketName, "run " + uuid + ".json", is, meta);
        */
    }
}