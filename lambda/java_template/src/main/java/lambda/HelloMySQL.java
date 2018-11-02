/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package lambda;

import com.amazonaws.services.lambda.runtime.ClientContext;
import com.amazonaws.services.lambda.runtime.CognitoIdentity;
import com.amazonaws.services.lambda.runtime.Context; 
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.LambdaLogger;
import faasinspector.register;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.LinkedList;
import java.util.Properties;
/**
 * uwt.lambda_test::handleRequest
 * @author wlloyd
 */
public class HelloMySQL implements RequestHandler<Request, Response>
{
    static String CONTAINER_ID = "/tmp/container-id";
    static Charset CHARSET = Charset.forName("US-ASCII");
    
    
    // Lambda Function Handler
    public Response handleRequest(Request request, Context context) {
        // Create logger
        LambdaLogger logger = context.getLogger();
        
        // Register function
        register reg = new register(logger);

        //stamp container with uuid
        Response r = reg.StampContainer();
        
        // *********************************************************************
        // Implement Lambda Function Here
        // *********************************************************************
        try 
        {
            Properties properties = new Properties();
            properties.load(new FileInputStream("db.properties"));
            
            String url = properties.getProperty("url");
            String username = properties.getProperty("username");
            String password = properties.getProperty("password");
            String driver = properties.getProperty("driver");
            
            // Manually loading the JDBC Driver is commented out
            // No longer required since JDBC 4
            //Class.forName(driver);
            Connection con = DriverManager.getConnection(url,username,password);

            PreparedStatement ps = con.prepareStatement("insert into mytable values('" + request.getName() + "','b','c');");
            ps.execute();
            ps = con.prepareStatement("select * from mytable;");
            ResultSet rs = ps.executeQuery();
            LinkedList<String> ll = new LinkedList<String>();
            while (rs.next())
            {
                logger.log("name=" + rs.getString("name"));
                ll.add(rs.getString("name"));
                logger.log("col2=" + rs.getString("col2"));
                logger.log("col3=" + rs.getString("col3"));
            }
            rs.close();
            con.close();
            r.setNames(ll);

        } 
        catch (Exception e) 
        {
            logger.log("Got an exception working with MySQL! ");
            logger.log(e.getMessage());
        }
        
        String hello = "Hello " + request.getName();

        //Print log information to the Lambda log as needed
        //logger.log("log message...");
        
        // Set return result in Response class, class is marshalled into JSON
        r.setValue(hello);
        
        return r;
    }
    
    // int main enables testing function from cmd line
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
        HelloMySQL lt = new HelloMySQL();
        
        // Create a request object
        Request req = new Request();
        
        // Grab the name from the cmdline from arg 0
        String name = (args.length > 0 ? args[0] : "");
        
        // Load the name into the request object
        req.setName(name);

        // Report name to stdout
        System.out.println("cmd-line param name=" + req.getName());
        
        // Test properties file creation
        Properties properties = new Properties();
        properties.setProperty("driver", "com.mysql.cj.jdbc.Driver");
        properties.setProperty("url","");
        properties.setProperty("username","");
        properties.setProperty("password","");
        try 
        {
          properties.store(new FileOutputStream("test.properties"),"");
        }
        catch (IOException ioe)
        {
          System.out.println("error creating properties file.")   ;
        }
        
        
        // Run the function
        //Response resp = lt.handleRequest(req, c);
        System.out.println("The MySQL Serverless can't be called directly without running on the same VPC as the RDS cluster.");
        Response resp = new Response();
        
        // Print out function result
        System.out.println("function result:" + resp.toString());
    }
}
