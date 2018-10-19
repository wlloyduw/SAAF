/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package uwt;

import com.amazonaws.services.lambda.runtime.ClientContext;
import com.amazonaws.services.lambda.runtime.CognitoIdentity;
import com.amazonaws.services.lambda.runtime.Context; 
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.LambdaLogger;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Random;
import java.util.UUID;
/**
 * uwt.lambda_test::handleRequest
 * @author wlloyd
 */
public class Hello implements RequestHandler<Request, Response>
{
    static String CONTAINER_ID = "/tmp/container-id";
    static Charset CHARSET = Charset.forName("US-ASCII");
    private String uuid = "unset";      // universal unique identifier for container - uniquely identifies runtime container on Lambda
    private int newcontainer = 0;       // integer that tracks if this lambda invocation created a new container (0=no, 1=yes)
    
    private static int STAMP_SUCCESS = 0;
    private static int STAMP_ERROR_READING_EXISTING_UUID = 1;
    private static int STAMP_ERROR_WRITING_NEW_UUID = 2;
    
    private static String STAMP_ERR_READING_EXISTING_UUID = "Error reading existing UUID";
    private static String STAMP_ERR_WRITING_NEW_UUID = "Error writing new UUID";
    private static String STAMP_ERR_UNKNOWN = "Unknown error obtaining UUID";

    // Lambda Function Handler
    public Response handleRequest(Request request, Context context) {
        LambdaLogger logger = context.getLogger();

        //stamp container with uuid
        int stampSuccess = StampContainer();
        if (stampSuccess != STAMP_SUCCESS)
        {
            if (stampSuccess == STAMP_ERROR_READING_EXISTING_UUID)
                return new Response(STAMP_ERR_READING_EXISTING_UUID,uuid);
            if (stampSuccess == STAMP_ERROR_WRITING_NEW_UUID)
                return new Response(STAMP_ERR_WRITING_NEW_UUID,uuid);
            return new Response(STAMP_ERR_UNKNOWN,uuid);
        }
        
        //get VM and CPU statistics
        VmCpuStat v2 = getVmCpuStat();
        long vuptime = getUpTime(v2);
        
        // *********************************************************************
        // Implement Lambda Function Here
        // *********************************************************************
        String hello = "Hello " + request.getName();

        //Print log information to the Lambda log as needed
        logger.log("UUID:" + uuid + " VM:" + vuptime + " | Function Success");
        
        // Return result as Response class, which is marshalled into JSON
        Response r = new Response(hello, uuid, vuptime, newcontainer);
        
        return r;
    }
    
    // Helper function - retrieves file as a String from file system
    public String getFileAsString(String filename)
    {
        File f = new File(filename);
        Path p = Paths.get(filename);
        String text = "";
        StringBuffer sb = new StringBuffer();
        if (f.exists()) 
        {
            try (BufferedReader br = Files.newBufferedReader(p))
            {
                while((text = br.readLine()) != null)
                {
                    sb.append(text);
                }
            }
            catch (IOException ioe)
            {
                sb.append("Error reading file=" + filename);
            }
        }
        return sb.toString();
    }
    
    // Stamps container with UUID - returns false on error
    private int StampContainer()
    {
        //Stamp container with a UUID
        File f = new File("/tmp/container-id");
        Path p = Paths.get("/tmp/container-id");
        if (f.exists()) 
        {
            newcontainer = 0;
            try (BufferedReader br = Files.newBufferedReader(p))
            {
                uuid = br.readLine();
                br.close();
            }
            catch (IOException ioe)
            {
                return STAMP_ERROR_READING_EXISTING_UUID;
            }
        }
        else
        {
            newcontainer = 1;            
            try (BufferedWriter bw = Files.newBufferedWriter(p, StandardCharsets.US_ASCII, StandardOpenOption.CREATE_NEW))
            {
                uuid = UUID.randomUUID().toString();
                bw.write(uuid);
                bw.close();
            }
            catch (IOException ioe)
            {
                return STAMP_ERROR_WRITING_NEW_UUID;
            }
        }
        return STAMP_SUCCESS;
    }
    
    class VmCpuStat
    {
        long cpuusr;
        long cpunice;
        long cpukrn;
        long cpuidle;
        long cpuiowait;
        long cpuirq;
        long cpusirq;
        long cpusteal;
        long btime;
        VmCpuStat(long cpuusr, long cpunice, long cpukrn, long cpuidle, 
                  long cpuiowait, long cpuirq, long cpusirq, long cpusteal)
        {
            this.cpuusr = cpuusr;
            this.cpunice = cpunice;
            this.cpukrn = cpukrn;
            this.cpuidle = cpuidle;
            this.cpuiowait = cpuiowait;
            this.cpuirq = cpuirq;
            this.cpusirq = cpusirq;
            this.cpusteal = cpusteal;
        }
        VmCpuStat() { }
    }
    
    public VmCpuStat getVmCpuStat()
    {
        String filename = "/proc/stat";
        File f = new File(filename);
        Path p = Paths.get(filename);
        String text = "";
        StringBuffer sb = new StringBuffer();
        if (f.exists()) 
        {
            try (BufferedReader br = Files.newBufferedReader(p))
            {
                text = br.readLine();
                String params[] = text.split(" ");
                VmCpuStat vcs = new VmCpuStat(Long.parseLong(params[2]),
                                              Long.parseLong(params[3]),
                                              Long.parseLong(params[4]),
                                              Long.parseLong(params[5]),
                                              Long.parseLong(params[6]),
                                              Long.parseLong(params[7]),
                                              Long.parseLong(params[8]),
                                              Long.parseLong(params[9]));
                while ((text = br.readLine()) != null && text.length() != 0) {
                    // get boot time in ms since epoch
                    if (text.contains("btime"))
                    {
                        String prms[] = text.split(" ");
                        vcs.btime = Long.parseLong(prms[1]);
                    }
                }
                br.close();
                return vcs;
            }
            catch (IOException ioe)
            {
                sb.append("Error reading file=" + filename);
                return new VmCpuStat();
            }
        }
        else
            return new VmCpuStat();
    }
    
    public long getUpTime(VmCpuStat vmcpustat)
    {

        return vmcpustat.btime;
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
        
        // Create an instance of the class
        Hello lt = new Hello();
        
        // Create a request object
        Request req = new Request();
        
        // Grab the name from the cmdline from arg 0
        String name = (args.length > 0 ? args[0] : "");
        
        // Load the name into the request object
        req.setName(name);

        // Report name to stdout
        System.out.println("cmd-line param name=" + req.getName());
        
        // Run the function
        Response resp = lt.handleRequest(req, c);
        
        // Print out function result
        System.out.println("function result:" + resp.toString());
    }
}
