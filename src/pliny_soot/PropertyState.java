/* Author: Vijay Murali */
package pliny_soot;

/** State of a particular property automaton
 *  For now it's just a wrapper for an Integer */
public class PropertyState {

    private int state;

    public PropertyState(int state) {
        this.state = state;
    }

    public int getState() {
        return state;
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || !(o instanceof PropertyState))
            return false;
        PropertyState ps = (PropertyState) o;
        return this.state == ps.getState();
    }

    @Override
    public int hashCode() {
        return state;
    }

    @Override
    public String toString() {
        return "" + state;
    }
}
