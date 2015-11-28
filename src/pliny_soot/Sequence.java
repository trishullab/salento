/* Author: Vijay Murali */

package pliny_soot;

import java.io.PrintStream;
import java.util.Map;
import java.util.HashMap;

/** A "sequence" along a path is in fact a set of sequences, i.e., a History
 * for every TypeStateObject along the path */
class Sequence {

    private Map<TypeStateObject,History> historyMap;

    public Sequence() {
        historyMap = new HashMap<TypeStateObject,History>();
    }

    public void addEvent(TypeStateObject t, Event e) {
        assert historyMap.containsKey(t) : "No history associated with object " + t;
        historyMap.get(t).addEvent(e);
    }

    public boolean containsTypeStateObject(TypeStateObject t) {
        return historyMap.containsKey(t);
    }

    public void addTypeStateObject(TypeStateObject t) {
        assert !historyMap.containsKey(t) : "History already associated with object " + t;
        historyMap.put(t, new History());
    }

    public int count() {
        int c = 0;
        for (TypeStateObject t : historyMap.keySet())
            if (historyMap.get(t).size() > 0)
                c++;
        return c;
    }

    public void print(PrintStream outfile) {
        if (historyMap.isEmpty())
            return;
        for (TypeStateObject t : historyMap.keySet())
            if (historyMap.get(t).size() > 0)
                outfile.println(t.getYoungestAndroidParent() + "#" + historyMap.get(t));
    }
}
