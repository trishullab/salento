/* Author: Vijay Murali */

package driver;

import java.util.List;
import soot.*;

/** A pair of API call and list of monitor states */
public class Event
{
    private SootMethod sigma;
    private List<MonitorState> monitorStates;
    private LocationInfo location;

    public Event(SootMethod sigma, List<MonitorState> monitorStates, LocationInfo location) {
        this.sigma = sigma;
        this.monitorStates = monitorStates;
        this.location = location;
    }

    public SootMethod getSigma() {
        return sigma;
    }

    public List<MonitorState> getMonitorStates() {
        return monitorStates;
    }

    public LocationInfo getLocationInfo() {
        return location;
    }

    @Override
    public String toString() {
        String s = Util.mySignature(sigma) + "[";
        for (MonitorState ps : monitorStates)
            s += ps.toString() + ",";
        if (s.charAt(s.length() - 1) == ',')
            s = s.substring(0, s.length() - 1);
        s += "][" + location + "]";
        return s;
    }
}
