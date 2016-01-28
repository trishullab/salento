/* Author: Vijay Murali */

package pliny_soot;

import java.util.List;
import java.util.ArrayList;
import java.io.PrintStream;

/** History of events */
public class History {
    private List<Event> events;

    public History() {
        events = new ArrayList<Event>();
    }

    public void addEvent(Event e) {
        events.add(e);
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
