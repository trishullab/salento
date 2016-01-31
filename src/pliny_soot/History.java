/* Author: Vijay Murali */

package pliny_soot;

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
        String s = "";
        for (Event e : events)
            s += e + ";";
        return s;
    }
}
