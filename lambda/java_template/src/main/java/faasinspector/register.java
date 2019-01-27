/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package faasinspector;

import com.amazonaws.services.lambda.runtime.LambdaLogger;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.UUID;
import lambda.Response;

/**
 *
 * @author wlloyd
 */
public class register 
{
    public static int STAMP_SUCCESS = 0;
    public static int STAMP_ERROR_READING_EXISTING_UUID = 1;
    public static int STAMP_ERROR_WRITING_NEW_UUID = 2;
    
    private static String STAMP_ERR_READING_EXISTING_UUID = "Error reading existing UUID";
    private static String STAMP_ERR_WRITING_NEW_UUID = "Error writing new UUID";
    private static String STAMP_ERR_UNKNOWN = "Unknown error obtaining UUID";
    private static String STAMP_ERR_NONE = "";
    
    private String uuid = "unset";      // universal unique identifier for container - uniquely identifies runtime container on Lambda
    private int newcontainer = 0;       // integer that tracks if this lambda invocation created a new container (0=no, 1=yes)
    private long vuptime = 0;
    private String sError = STAMP_ERR_NONE;
    
    private LambdaLogger logger;
    
    public register(LambdaLogger l)
    {
        this.logger = l;
    }
    
    // Stamps container with UUID - returns false on error
    public Response StampContainer()
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
                sError = STAMP_ERR_READING_EXISTING_UUID; 
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
                sError = STAMP_ERR_WRITING_NEW_UUID;
            }
        }
        //get VM and CPU statistics
        VmCpuStat v2 = getVmCpuStat();
        long vuptime = getUpTime(v2);
        
        //Print log information to the Lambda log as needed
        if (!sError.isEmpty())
            logger.log("UUID:" + uuid + " VM:" + vuptime + " | " + sError );
        
        Response r = new Response();
        r.setError(sError);
        r.setUuid(uuid);
        r.setVmuptime(vuptime);
        r.setNewcontainer(newcontainer);
        r.setCpuType(getCpuType());
        return r;
    }
    
    public class VmCpuStat
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

    public String getUuid()
    {
        return uuid;
    }
    
    public int getNewContainer()
    {
        return newcontainer;
    }
    
    public long getVmUpTime()
    {
        return vuptime;
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
    
    public String getCpuType()
    {
        String text = getFileAsString("/proc/cpuinfo");
        int start = text.indexOf("name") + 7;
        int end = start + text.substring(start).indexOf(":");
        String cpuType = text.substring(start,end).trim();
        return cpuType;
    }
    
}
