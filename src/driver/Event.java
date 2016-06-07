/* Author: Vijay Murali */

package driver;

import java.util.List;
import java.util.ArrayList;
import soot.*;

import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;

/** A pair of API call and list of monitor states */
public class Event
{
    private SootMethod sigma;
    private List<MonitorState> monitorStates;

    /* Primitives for Gson */
    @Expose
    @SerializedName("call") 
    private String sigma_;
    @Expose
    @SerializedName("states") 
    private List<Integer> monitorStates_;

    @Expose
    private LocationInfo location;

    public Event(SootMethod sigma, List<MonitorState> monitorStates, LocationInfo location) {
        this.sigma = sigma;
        this.monitorStates = monitorStates;
        this.location = location;

        this.sigma_ = Util.mySignature(sigma);
        this.monitorStates_ = new ArrayList<Integer>();
        for (MonitorState s : monitorStates)
            this.monitorStates_.add(s.getState());
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
