/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package uwt;

import java.lang.annotation.Native;

/**
 *
 * @author wlloyd
 */
public class Response {
    String value;
    String uuid;
    String error;
    long vmuptime;
    int newcontainer;
    
    public String getValue()
    {
        return value;
    }
    public void setValue(String value)
    {
        this.value = value;
    }
    public String getUuid()
    {
        return uuid;
    }
    public void setUuid(String uuid)
    {
        this.uuid = uuid;
    }
    public String getError()
    {
        return error;
    }
    public void setError(String err)
    {
        this.error = err;
    }
    public long getVmuptime()
    {
        return this.vmuptime;
    }
    public void setVmuptime(long vmuptime)
    {
        this.vmuptime = vmuptime;
    }
    public int getNewcontainer()
    {
        return this.newcontainer;
    }
    public void setNewcontainer(int newcontainer)
    {
        this.newcontainer = newcontainer;
    }
        
    public Response(String value, String uuid)
    {
        this.value = value;
        this.uuid = uuid;
    }
    public Response(String value, String uuid, long vuptime, int newcontainer)
    {
        this.value = value;
        this.uuid = uuid;
        this.vmuptime = vuptime;
        this.newcontainer = newcontainer;
    }
    public Response()
    {
        
    }
    
    @Override
    public String toString()
    {
        return "value=" + this.getValue() + "\nuuid=" + this.getUuid() + "\nvmuptime=" + this.getVmuptime();
    }
    

}
