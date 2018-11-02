/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package lambda;

import faasinspector.fiResponse;
import java.lang.annotation.Native;
import java.util.List;

/**
 *
 * @author wlloyd
 */
public class Response extends fiResponse {
    
    //
    // User Defined Attributes
    //
    //
    // ADD getters and setters for custom attributes here.
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

    public List<String> names;
    public List<String> getNames()
    {
        return this.names;
    }
    public void setNames(List<String> names)
    {
        this.names = names;
    }
    
    @Override
    public String toString()
    {
        return "value=" + this.getValue() + super.toString(); 
    }

}
