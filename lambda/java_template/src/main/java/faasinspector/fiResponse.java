/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package faasinspector;

/**
 *
 * @author wlloyd
 */
public class fiResponse 
{
//
    //
    //
    // Faas Inspector return attributes
    //
    //
    private String cpuType;
    private String uuid;
    private String error;
    long vmuptime;
    long runtime;
    int newcontainer;

    public fiResponse()                             
    {          
        
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
    
    public long getRuntime()
    {
        return this.runtime;
    }
    
    public void setRuntime(long runtime)
    {
        this.runtime = runtime;
    }
    
    public int getNewcontainer()                  
    {        
        return this.newcontainer;  
    }
    
    public void setNewcontainer(int newcontainer) 
    { 
        this.newcontainer = newcontainer; 
    }
    
    public String getCpuType()
    {
        return this.cpuType;
    }
    public void setCpuType(String cputype)
    {
        this.cpuType = cputype;
    }
    
    @Override
    public String toString()
    {
        return "\nuuid=" + this.getUuid() + "\nvmuptime=" + this.getVmuptime() + "\ncputype=" + this.getCpuType();
    }
    
}
