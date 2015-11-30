/* Author: Vijay Murali */
package pliny_soot.properties;

import pliny_soot.*;

/** State of an equality property automaton */
public class EqualityPropertyState implements PropertyState {

    public static final int TRUE = 1;
    public static final int FALSE = 0;

    private int state;

    public EqualityPropertyState(int state) {
        assert state == TRUE || state == FALSE : "invalid state: " + state;
        this.state = state;
    }

    /** String representation of this state */
    @Override
    public String toString() {
        if (state == TRUE) return "1";
        else return "0";
    }
}
