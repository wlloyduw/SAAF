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
    private String uuid;
    private String error;
    long vmuptime;
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
    
    public int getNewcontainer()                  
    {        
        return this.newcontainer;  
    }
    
    public void setNewcontainer(int newcontainer) 
    { 
        this.newcontainer = newcontainer; 
    }
    
    @Override
    public String toString()
    {
        return "\nuuid=" + this.getUuid() + "\nvmuptime=" + this.getVmuptime();
    }
    
}
