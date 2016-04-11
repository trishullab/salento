/* Author: Vijay Murali */

package driver;

import soot.jimple.Stmt;

/** A predicate in a transition in a monitor */
public interface Predicate {

    /** Returns true iff the predicate is enabled for the statement stmt */
    public boolean enabled(StmtInstance stmt);
}
