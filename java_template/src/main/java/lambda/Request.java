package lambda;

/**
 *
 * @author Wes Lloyd
 */
public class Request {

    String name;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Request(String name) {
        this.name = name;
    }

    public Request() {

    }
}
