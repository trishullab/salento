/* Author: Vijay Murali */

package pliny_soot;

import java.util.List;
import soot.*;

/** A pair of API call and list of property automaton states */
public class Event
{
    private SootMethod sigma;
    private List<PropertyState> propertyStates;

    public Event(SootMethod sigma, List<PropertyState> propertyStates) {
        this.sigma = sigma;
        this.propertyStates = propertyStates;
    }

    public SootMethod getSigma() {
        return sigma;
    }

    public List<PropertyState> getPropertyStates() {
        return propertyStates;
    }

    @Override
    public String toString() {
        String s = Util.mySignature(sigma) + "[";
        for (PropertyState ps : propertyStates)
            s += ps.toString() + ",";
        if (s.charAt(s.length() - 1) == ',')
            s = s.substring(0, s.length() - 1);
        s += "]";
        return s;
    }
}
