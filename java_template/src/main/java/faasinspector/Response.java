package faasinspector;

/**
 * A basic Response object that can be consumed by FaaS Inspector
 * to be used as output.
 * 
 * @author Wes Lloyd
 * @author Robert Cordingly
 */
public class Response {
    //
    // User Defined Attributes
    //
    //
    // ADD getters and setters for custom attributes here.
    //

    // Return value
    private String value;

    public String getValue() {
        return value;
    }

    public void setValue(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return "value=" + this.getValue() + super.toString();
    }
}
