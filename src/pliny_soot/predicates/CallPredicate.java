/* Author: Vijay Murali */

package pliny_soot.predicates;

import pliny_soot.*;

import soot.Unit;
import soot.SootMethod;

import soot.jimple.Stmt;
import soot.jimple.InvokeExpr;

/** A predicate that enables/disables on a particular API call */
public class CallPredicate implements Predicate {

    private String method;

    public CallPredicate(String method) {
        this.method = method;
    }

    public static void apply(Unit ustmt) {
    }

    public boolean enabled(Unit ustmt) {
        Stmt stmt = (Stmt) ustmt;

        if (!stmt.containsInvokeExpr())
            return false;

        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        SootMethod callee = invokeExpr.getMethod();

        return Util.mySignature(callee).equals(method);
    }
}
