/* Author: Vijay Murali */

package driver;

import soot.jimple.Stmt;

/** A transition in a monitor */
public class Transition {

    private MonitorState from;
    private MonitorState to;
    private Predicate predicate;

    public Transition(MonitorState from, MonitorState to, Predicate predicate) {
        this.from = from;
        this.to = to;
        this.predicate = predicate;

        assert predicate != null : "invalid predicate in trans " + from + "->" + to;
    }

    public MonitorState from() {
        return from;
    }

    public MonitorState to() {
        return to;
    }

    public boolean enabled(StmtInstance stmt) {
        return predicate.enabled(stmt);
    }
}
