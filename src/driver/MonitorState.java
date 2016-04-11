/* Author: Vijay Murali */
package driver;

/** State of a particular monitor automaton
 *  For now it's just a wrapper for an Integer */
public class MonitorState {

    private int state;

    public MonitorState(int state) {
        this.state = state;
    }

    public int getState() {
        return state;
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || !(o instanceof MonitorState))
            return false;
        MonitorState ps = (MonitorState) o;
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
