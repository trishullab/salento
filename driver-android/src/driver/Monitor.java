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

import driver.predicates.*;

import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.io.*;

import soot.jimple.Stmt;

/** A monitor */
public class Monitor {
    
    /** The internal automaton state */
    private MonitorState state;

    /** List of transitions between states */
    List<Transition> transitions;

    public Monitor() {
        state = new MonitorState(0);
        transitions = new ArrayList<Transition>();
    }

    public Monitor(List<Transition> transitions) {
        state = new MonitorState(0);
        this.transitions = transitions;
    }

    public MonitorState getState() {
        return state;
    }

    public List<Transition> getTransitions() {
        return transitions;
    }

    public void resetState() {
        state = new MonitorState(0);
    }

    public void addTransition(Transition t) {
        transitions.add(t);
    }

    /** Update internal state of this automaton if a transition is enabled */
    public void post(StmtInstance stmt) {
        boolean stateChange;
        do {
            stateChange = false;
            int enabled = 0;
            MonitorState nextState = state;
            for (Transition t : transitions)
                if (state.equals(t.from()) && t.enabled(stmt)) {
                    nextState = t.to();
                    stateChange = true;
                    enabled++;
                }

            assert enabled <= 1 : "more than one enabled trans for " + stmt + " from " + state;
            state = nextState;
        } while (stateChange);
    }



    /* Static methods */


    /** Read monitors from a file and create the automata */
    public static List<Monitor> readMonitors(File f) throws FileNotFoundException, IOException {
        assert f.exists() : "cannot find monitors file " + f;

        BufferedReader br = new BufferedReader(new FileReader(f));
        String line;
        List<Monitor> monitors = new ArrayList<Monitor>();

        Monitor p = null;
        while ((line = br.readLine()) != null) {
            if (line.startsWith("#") || line.trim().equals("")) /* comment */
                continue;

            if (line.startsWith("m#")) { /* new automaton */
                if (p != null)
                    monitors.add(p);
                p = new Monitor();
                continue;
            }

            Pattern regex = Pattern.compile("(\\d+)->(\\d+) (\\w+) (.*)");
            Matcher m = regex.matcher(line.trim());

            assert m.matches() : "malformed monitors transition: " + line;

            try {
                MonitorState from = new MonitorState(Integer.parseInt(m.group(1)));
                MonitorState to = new MonitorState(Integer.parseInt(m.group(2)));
                String type = m.group(3);
                String rest = m.group(4);

                /* Add new predicate types here*/
                Transition t = new Transition(from, to,
                        type.equals("equality")  ? new EqualityPredicate(rest) :
                        type.equals("call")      ? new CallPredicate(rest) :
                        type.equals("arity")     ? new ArityPredicate(rest) :
                        type.equals("argvalRE")  ? new ArgValueREPredicate(rest) :
                        type.equals("exception") ? new ExceptionPredicate(rest) :
                        null);
                p.addTransition(t);
            } catch (NumberFormatException e) {
                assert false : "invalid state: " + line;
            }
        }

        if (p != null)
            monitors.add(p);

        return monitors;
    }

    /** Update global information regarding predicates according to this statement */
    public static void apply(Stmt stmt) {
        EqualityPredicate.apply(stmt);
        CallPredicate.apply(stmt);
        ArityPredicate.apply(stmt);
        ArgValueREPredicate.apply(stmt);
        ExceptionPredicate.apply(stmt);
    }
}
