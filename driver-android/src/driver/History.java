/*
Copyright 2017 Rice University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
/* Author: Vijay Murali */

package driver;

import java.util.List;
import java.util.ArrayList;
import java.io.PrintStream;

import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;

/** History of events */
public class History {
    @Expose
    @SerializedName("sequence") 
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
