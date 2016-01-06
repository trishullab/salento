/* Author: Vijay Murali */

package pliny_soot;

import soot.jimple.Stmt;

/** A transition in a property automaton */
public class Transition {

    private PropertyState from;
    private PropertyState to;
    private Predicate predicate;

    public Transition(PropertyState from, PropertyState to, Predicate predicate) {
        this.from = from;
        this.to = to;
        this.predicate = predicate;

        assert predicate != null : "invalid predicate in trans " + from + "->" + to;
    }

    public PropertyState from() {
        return from;
    }

    public PropertyState to() {
        return to;
    }

    public boolean enabled(Stmt stmt) {
        return predicate.enabled(stmt);
    }
}
