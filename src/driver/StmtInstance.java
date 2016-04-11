/* Author: Vijay Murali */

package driver;

import soot.SootClass;
import soot.jimple.Stmt;

/** A thin wrapper for an instance of a statement along a path with some additional info */
public class StmtInstance {

    private Stmt stmt;
    private SootClass exceptionThrown;

    public StmtInstance (Stmt stmt) {
        this.stmt = stmt;
    }

    public Stmt getStmt() {
        return stmt;
    }

    public boolean isExceptionThrown() {
        return exceptionThrown != null;
    }

    public SootClass getExceptionThrown() {
        return exceptionThrown;
    }

    public void setExceptionThrown(SootClass e) {
        this.exceptionThrown = e;
    }
}
