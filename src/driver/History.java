/* Author: Vijay Murali */

package driver;

import java.util.List;
import java.util.ArrayList;
import java.io.PrintStream;

/** History of events */
public class History {
    private List<Event> events;

    /** Flag that tells whether this history has been finalized.
     * No further events can be collected on finalized histories. */
    private boolean finalized = false;

    public History() {
        events = new ArrayList<Event>();
    }

    public void addEvent(Event e) {
        assert !finalized : "Event " + e + " cannot be added to finalized history!";
        events.add(e);
    }

    public void finalize() {
        finalized = true;
    }

    public boolean isFinalized() {
        return finalized;
    }

    public List<Event> getEvents() {
        return events;
    }

    public int size() {
        return events.size();
    }

    public void clear() {
        events.clear();
    }

    public void print(PrintStream out) {
        for (Event e : events)
            out.print(e + " ");
    }

    @Override
    public String toString() {
        if (events.size() == 0)
            return "";

        String s = "";
        if (Options.printSequenceStartEnd) {
            /* print START with default monitor states */
            s += "\"START\"[";
            int nprops = events.get(0).getMonitorStates().size();
            for (int i = 0; i < nprops; i++)
                s += "0" + (i == nprops-1? "" : ",");
            s += "][];";
        }
        
        for (Event e : events)
            s += e + ";";

        if (Options.printSequenceStartEnd) {
            /* print END with monitor states of the last event */
            s += "\"END\"[";
            for (MonitorState ps : events.get(events.size()-1).getMonitorStates())
                s += ps.toString() + ",";
            if (s.charAt(s.length() - 1) == ',')
                s = s.substring(0, s.length() - 1);
            s += "][];";
        }
        return s;
    }
}
