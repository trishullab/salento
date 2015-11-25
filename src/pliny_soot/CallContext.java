/* Author: Vijay Murali */

package pliny_soot;

import soot.*;
import soot.toolkits.graph.UnitGraph;

public class CallContext {

    private Unit stmt;
    private UnitGraph cfg;

    public CallContext(Unit stmt, UnitGraph cfg) {
        this.stmt = stmt;
        this.cfg = cfg;
    }

    public Unit getStmt() {
        return stmt;
    }

    public UnitGraph getCfg() {
        return cfg;
    }
}
