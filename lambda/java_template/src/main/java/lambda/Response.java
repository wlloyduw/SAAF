/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package lambda;

import java.lang.annotation.Native;

/**
 *
 * @author wlloyd
 */
public class Response {
    
    //
    // User Defined Attributes
    //
    //
    // ADD Customer attributes getters and setters here
    //

    // Return value
    private String value;
    public String getValue()
    {
        return value;
    }
    public void setValue(String value)
    {
        this.value = value;
    }
    


    
    
    //
    //
    //
    // Faas Inspector required return attributes
    //
    //
    // DO NOT MODIFY
    //
    //
    private String uuid;
    private String error;
    long vmuptime;
    int newcontainer;

    public Response()                             {                                   }
    public String getUuid()                       {        return uuid;               }
    public void setUuid(String uuid)              {        this.uuid = uuid;          }
    public String getError()                      {        return error;              }
    public void setError(String err)              {        this.error = err;          }
    public long getVmuptime()                     {        return this.vmuptime;      }
    public void setVmuptime(long vmuptime)        {        this.vmuptime = vmuptime;  }
    public int getNewcontainer()                  {        return this.newcontainer;  }
    public void setNewcontainer(int newcontainer) { this.newcontainer = newcontainer; }
    
    @Override
    public String toString()
    {
        return "value=" + this.getValue() + "\nuuid=" + this.getUuid() + "\nvmuptime=" + this.getVmuptime();
    }

}
