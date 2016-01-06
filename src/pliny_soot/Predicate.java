/* Author: Vijay Murali */

package pliny_soot;

import soot.Unit;

/** A predicate in a transition in a property automaton */
public interface Predicate {

    /** Returns true iff the predicate is enabled for the statement stmt */
    public boolean enabled(Unit stmt);
}
